import google.generativeai as genai
import google.ai.generativelanguage as glm
from dotenv import load_dotenv
import time
import os
import json

from config import GEMINI_MODEL_NAME, TOOL_CALL_PAUSE_SECONDS, PROMPT_DIRECTORY, SHOW_AGENT_THOUGHTS, SHOW_DEBUG_MESSAGES
from logging_handler import log_agent_thought, log_agent_response, log_tool_call, log_tool_output, log_error, log_system_message, log_debug, log_success, log_user_input
from utils.colors import Colors
from tools.file_system_tools import file_system_tool_definitions, file_system_functions
from tools.execution_tools import execution_tool_definitions, execution_functions
from tools.control_tools import control_tool_definitions, control_functions, USER_INPUT_REQUIRED, USER_RESPONSE
from tools.internet_tools import internet_tool_definitions, internet_functions
from tools.advanced_tools import advanced_tool_definitions, advanced_functions

load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

class Agent:
    def __init__(self):
        self.system_instruction = self._load_system_instruction_from_files()

        self.all_tool_definitions = glm.Tool(
            function_declarations=(
                list(file_system_tool_definitions.function_declarations) +
                list(execution_tool_definitions.function_declarations) +
                list(control_tool_definitions.function_declarations) +
                list(internet_tool_definitions.function_declarations) +
                list(advanced_tool_definitions.function_declarations)
            )
        )

        self.available_functions = {
            **file_system_functions,
            **execution_functions,
            **control_functions,
            **internet_functions,
            **advanced_functions
        }

        self.model = genai.GenerativeModel(
            GEMINI_MODEL_NAME,
            tools=[self.all_tool_definitions],
            system_instruction=self.system_instruction
        )
        self.chat = self.model.start_chat(history=[])

    def _load_system_instruction_from_files(self):
        all_instructions = []
        try:
            prompt_files = sorted([f for f in os.listdir(PROMPT_DIRECTORY) if f.endswith('.txt')])
            if not prompt_files:
                log_error(f"Tidak ada file instruksi (.txt) ditemukan di direktori: {PROMPT_DIRECTORY}.")
                return "Anda adalah AI yang cerdas dan mampu berkomunikasi serta menggunakan tool."
            for filename in prompt_files:
                filepath = os.path.join(PROMPT_DIRECTORY, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    all_instructions.append(f.read())
                log_debug(f"Memuat instruksi dari: {filename}")
            return "\n\n".join(all_instructions)
        except Exception as e:
            log_error(f"Gagal memuat instruksi sistem dari file: {e}")
            return "Anda adalah AI yang cerdas dan mampu berkomunikasi serta menggunakan tool."


    def _execute_tool_call(self, call):
        function_name = call.name
        function_args = {k: v for k, v in call.args.items()}
        log_tool_call(function_name, function_args)

        try:
            if function_name != 'ask_user_for_input':
                globals()['USER_INPUT_REQUIRED'] = False
            
            function_output_json = self.available_functions[function_name](**function_args)
            
            try:
                output_dict = json.loads(function_output_json)
                log_tool_output(function_name, output_dict)
            except (json.JSONDecodeError, TypeError):
                log_tool_output(function_name, function_output_json)

            return glm.Part(
                function_response=glm.FunctionResponse(
                    name=function_name,
                    response={"result": function_output_json}
                )
            )
        except Exception as e:
            error_message = f"Gagal mengeksekusi fungsi {function_name}: {e}"
            log_error(error_message)
            error_json = json.dumps({"success": False, "data": error_message})
            return glm.Part(
                function_response=glm.FunctionResponse(
                    name=function_name,
                    response={"error": error_json}
                )
            )

    def _get_llm_response(self, prompt_or_tool_output):
        try:
            response = self.chat.send_message(prompt_or_tool_output)
            
            if SHOW_AGENT_THOUGHTS:
                thought_text = " ".join([p.text for p in response.candidates[0].content.parts if p.text]).strip()
                if thought_text:
                    log_agent_thought(f"Pemikiran:\n{thought_text}")

            while response.candidates and response.candidates[0].content and any(part.function_call for part in response.candidates[0].content.parts):
                tool_calls = [part.function_call for part in response.candidates[0].content.parts if part.function_call]
                
                tool_responses_parts = []
                for call in tool_calls:
                    response_part = self._execute_tool_call(call)
                    tool_responses_parts.append(response_part)
                    time.sleep(TOOL_CALL_PAUSE_SECONDS)
                
                if globals().get('USER_INPUT_REQUIRED'):
                    return None

                response = self.chat.send_message(tool_responses_parts)
                
                if SHOW_AGENT_THOUGHTS:
                    thought_text = " ".join([p.text for p in response.candidates[0].content.parts if p.text]).strip()
                    if thought_text:
                        log_agent_thought(f"Pemikiran setelah tool call:\n{thought_text}")

            return response
        except genai.types.BlockedPromptException as e:
            log_error(f"Permintaan Anda diblokir karena alasan keamanan. Detail: {e}")
            return None
        except Exception as e:
            log_error(f"Terjadi kesalahan saat berkomunikasi dengan model: {e}")
            return None

    def _was_signal_tool_called(self, signal_name):
        if not self.chat.history: return False
        for message in reversed(self.chat.history):
            if message.role == 'user':
                return False
            if message.role == 'model':
                for part in message.parts:
                    if part.function_call and part.function_call.name == signal_name:
                        return True
        return False

    def run_task(self, user_task):
        log_system_message(f"AI memproses permintaan Anda: '{user_task}'")

        log_system_message(f"--- Memulai Tahap Penilaian & Perencanaan ---")
        planning_prompt = (
            f"Pengguna telah memberikan tugas: '{user_task}'.\n\n"
            "Analisis permintaan ini. Apakah pengguna memberikan file instruksi (misalnya, 'baca tugas.txt')?\n"
            "1. Jika YA, dan file itu ada, gunakan kontennya sebagai rencana Anda. Anda TIDAK perlu membuat `todo.md` baru. Cukup mulai eksekusi berdasarkan file itu.\n"
            "2. Jika TIDAK, atau jika tugasnya sederhana, buat rencana langkah-demi-langkah di `todo.md` menggunakan `write_file`.\n"
            "3. Jika Anda kurang informasi untuk membuat rencana, gunakan `web_search` atau `ask_user_for_input` DULU.\n"
            "   - Setelah rencana siap (baik dari file atau dibuat baru), Anda HARUS memanggil `signal_task_in_progress()` untuk memulai eksekusi. Ini adalah sinyal untuk saya agar melanjutkan."
        )
        initial_response = self._get_llm_response(planning_prompt)
        
        while not initial_response and globals().get('USER_INPUT_REQUIRED'):
            user_input = input(f"{Colors.BOLD}{Colors.GREEN}Input Anda: {Colors.RESET}").strip()
            log_user_input(user_input)
            user_feedback_part = glm.Part(
                function_response=glm.FunctionResponse(
                    name="ask_user_for_input",
                    response={"result": json.dumps({"success": True, "data": f"Pengguna merespons: {user_input}"})}
                )
            )
            globals()['USER_INPUT_REQUIRED'] = False
            initial_response = self._get_llm_response(user_feedback_part)
            if not initial_response and not globals().get('USER_INPUT_REQUIRED'):
                 log_error("Gagal mendapatkan respons dari AI setelah input pengguna. Sesi dihentikan.")
                 return

        if not self._was_signal_tool_called("signal_task_in_progress"):
            if initial_response and initial_response.candidates and initial_response.candidates[0].content:
                final_text = " ".join([p.text for p in initial_response.candidates[0].content.parts if p.text]).strip()
                if final_text: log_agent_response(final_text)
            log_system_message("[Han Agent: Sesi berakhir setelah tahap perencanaan (tidak ada sinyal lanjut).]")
            return
        
        log_success("--- Perencanaan Selesai. Memulai Eksekusi ---")


        iteration_count = 0
        MAX_ITERATIONS = 50
        
        next_prompt = (
            "Rencana telah dibuat. Sekarang eksekusi rencana tersebut langkah demi langkah. "
            "Baca `todo.md`, lakukan langkah berikutnya, dan teruskan sampai selesai. "
            "Hanya panggil `signal_task_complete` jika SEMUA tugas sudah selesai. "
            "Hanya panggil `ask_user_for_input` jika Anda benar-benar membutuhkan bantuan."
        )

        while iteration_count < MAX_ITERATIONS:
            iteration_count += 1
            log_system_message(f"--- Iterasi {iteration_count} ---")
            
            response = self._get_llm_response(next_prompt)

            if globals().get('USER_INPUT_REQUIRED'):
                user_input = input(f"{Colors.BOLD}{Colors.GREEN}Input Anda: {Colors.RESET}").strip()
                log_user_input(user_input)
                user_feedback_part = glm.Part(
                    function_response=glm.FunctionResponse(
                        name="ask_user_for_input",
                        response={"result": json.dumps({"success": True, "data": f"Pengguna merespons: {user_input}"})}
                    )
                )
                globals()['USER_INPUT_REQUIRED'] = False
                
                next_prompt = user_feedback_part 
                continue

            if self._was_signal_tool_called("signal_task_complete"):
                log_success("--- TUGAS SELESAI DIKERJAKAN (menurut sinyal AI) ---")
                try:
                    final_summary = "AI tidak memberikan ringkasan."
                    for msg in reversed(self.chat.history):
                        if msg.role == 'user': break
                        if msg.role == 'model':
                            for part in msg.parts:
                                if part.function_call and part.function_call.name == "signal_task_complete":
                                    final_summary = part.function_call.args.get('final_summary', 'Tidak ada ringkasan yang diberikan.')
                                    break
                            if final_summary != "AI tidak memberikan ringkasan.": break
                    log_agent_response(f"Ringkasan Akhir dari AI:\n{final_summary}")
                except (IndexError, KeyError):
                    log_agent_response("AI menyelesaikan tugas tanpa memberikan ringkasan akhir.")
                break 

            if not response:
                log_error("Terjadi error atau prompt diblokir. Sesi eksekusi dihentikan.")
                break
.
            tool_output_summary = ""
            if self.chat.history and self.chat.history[-1].role == 'tool':
                tool_responses = self.chat.history[-1].parts
                summaries = [f"- Tool '{p.function_response.name}' dipanggil. Hasil: {json.dumps(p.function_response.response)}" for p in tool_responses]
                tool_output_summary = "\n".join(summaries)
            
            final_text = ""
            if response.candidates and response.candidates[0].content:
                 final_text = " ".join([p.text for p in response.candidates[0].content.parts if p.text]).strip()

            next_prompt = (
                "Lanjutkan ke langkah berikutnya berdasarkan rencana Anda. "
                "Berikut adalah ringkasan dari apa yang baru saja Anda lakukan:\n"
                f"{tool_output_summary if tool_output_summary else '(Tidak ada tool yang dipanggil di giliran terakhir.)'}\n"
                f"{'AI juga mengatakan: ' + final_text if final_text else ''}\n\n"
                "Apa tindakan Anda selanjutnya?"
            )
        else:
            log_error(f"Mencapai batas iterasi ({MAX_ITERATIONS}). Tugas dihentikan secara paksa.")
            
        log_system_message(f"--- Sesi Eksekusi Selesai ---")