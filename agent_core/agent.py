import google.generativeai as genai
import google.ai.generativelanguage as glm
from dotenv import load_dotenv
import time
import os

from config import GEMINI_MODEL_NAME, TOOL_CALL_PAUSE_SECONDS, PROMPT_DIRECTORY
from logging_handler import log_agent_thought, log_agent_response, log_tool_call, log_tool_output, log_error, log_system_message, log_debug, log_success
from utils.colors import Colors
from tools.file_system_tools import file_system_tool_definitions, file_system_functions
from tools.execution_tools import execution_tool_definitions, execution_functions

load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

class Agent:
    def __init__(self):
        self.system_instruction = self._load_system_instruction_from_files()

        self.all_tool_definitions = glm.Tool(
            function_declarations=(
                list(file_system_tool_definitions.function_declarations) +
                list(execution_tool_definitions.function_declarations)
            )
        )

        self.available_functions = {
            **file_system_functions,
            **execution_functions
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
                log_error(f"Tidak ada file instruksi (.txt) ditemukan di direktori: {PROMPT_DIRECTORY}. Pastikan Anda membuat file-file instruksi.")
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
        function_args_raw = call.args

        function_args = {}
        for k, v in function_args_raw.items():
            if hasattr(v, '__iter__') and not isinstance(v, str):
                function_args[k] = list(v)
            else:
                function_args[k] = v

        log_tool_call(function_name, function_args)

        try:
            function_output = self.available_functions[function_name](**function_args)
            log_tool_output(function_name, function_output)
            return glm.Part(
                function_response=glm.FunctionResponse(
                    name=function_name,
                    response={"result": function_output}
                )
            )
        except Exception as e:
            error_message = f"Gagal mengeksekusi fungsi {function_name}: {e}"
            log_error(error_message)
            return glm.Part(
                function_response=glm.FunctionResponse(
                    name=function_name,
                    response={"error": error_message}
                )
            )

    def _get_llm_response(self, prompt_or_tool_output):
        try:
            response = self.chat.send_message(prompt_or_tool_output)

            while response.candidates and response.candidates[0].content and any(part.function_call for part in response.candidates[0].content.parts):
                tool_calls = [part.function_call for part in response.candidates[0].content.parts if part.function_call]
                tool_responses_parts = []
                for call in tool_calls:
                    tool_responses_parts.append(self._execute_tool_call(call))
                    time.sleep(TOOL_CALL_PAUSE_SECONDS)

                if tool_responses_parts:
                    response = self.chat.send_message(tool_responses_parts)
                else:
                    break

            return response
        except genai.types.BlockedPromptException as e:
            log_error(f"Permintaan Anda diblokir karena alasan keamanan. Detail: {e}")
            return None
        except Exception as e:
            log_error(f"Terjadi kesalahan saat berkomunikasi dengan model: {e}")
            return None


    def run_task(self, user_task):
        log_system_message(f"AI memproses permintaan Anda: '{user_task}'")

        initial_prompt = (
            f"Pengguna telah memberikan input: '{user_task}'.\n\n"
            "Berdasarkan definisi 'Tugas yang Harus Dijalankan' dan 'Respons Langsung/Informatif' yang diberikan di instruksi sistem Anda (yang telah dimuat dari berbagai file), "
            "tentukan apakah ini adalah sebuah tugas yang memerlukan perencanaan dan tool, atau dapat direspons langsung. "
            "Jika ini adalah 'tugas', buat RENCANA DETAIL dalam daftar berpoin. Setelah rencana, nyatakan 'PLAN SIAP'. "
            "Jika ini adalah 'respons langsung/informatif' atau Anda perlu klarifikasi, berikan respons Anda tanpa 'PLAN SIAP', "
            "dan **tanpa `[LANJUTKAN]` atau `TUGAS SELESAI`**. Anda akan berhenti setelah ini. "
            "Jika ini adalah tugas dan Anda sudah siap dengan rencana, tulis 'PLAN SIAP' setelah rencana Anda."
        )
        log_system_message(f"--- Memulai Tahap Penilaian/Perencanaan ---")
        planning_response = self._get_llm_response(initial_prompt)
        if not planning_response or not planning_response.candidates or not planning_response.candidates[0].content:
            log_error(f"Gagal mendapatkan respons awal dari AI.")
            return

        plan_text_parts = [p.text for p in planning_response.candidates[0].content.parts if p.text]
        plan_text = " ".join(plan_text_parts).strip()
        
        log_agent_thought(f"Respons Awal:\n{plan_text}")

        if "TUGAS SELESAI" in plan_text.upper():
            log_success(f"--- Tugas Selesai Dikerjakan oleh Agent ---")
            return
        
        if "PLAN SIAP" not in plan_text.upper():
            log_system_message(f"[Han Agent: Respon ini tidak memerlukan eksekusi iteratif. Sesi ini berakhir untuk menunggu input berikutnya.]")
            return

        log_system_message(f"--- Perencanaan Selesai. Memulai Eksekusi ---")

        iteration_count = 0
        MAX_ITERATIONS = 20

        while iteration_count < MAX_ITERATIONS:
            iteration_count += 1
            log_system_message(f"--- Iterasi {iteration_count} ---")
            log_system_message(f"[AI menentukan langkah selanjutnya...]")

            execution_prompt = (
                f"Tugas yang diberikan: '{user_task}'\n"
                f"Rencana Anda saat ini:\n{plan_text}\n"
                f"Lanjutkan dengan langkah berikutnya dari rencana Anda. Panggil fungsi tool yang diperlukan. "
                f"Setelah setiap tindakan (panggilan tool), REFLEKSIKAN hasilnya dan berikan update status. "
                f"Jika Anda telah membuat kemajuan dan ingin melanjutkan ke langkah berikutnya TANPA input pengguna, akhiri respons Anda dengan `[LANJUTKAN]` di baris terpisah."
                f"Jika tugas sudah selesai, berikan ringkasan akhir dan nyatakan dengan jelas 'TUGAS SELESAI'. "
                f"Jika ada masalah atau Anda memerlukan informasi lebih lanjut dari pengguna untuk melanjutkan, "
                f"jelaskan masalahnya atau ajukan pertanyaan klarifikasi dengan jelas dan akhiri respons Anda TANPA `[LANJUTKAN]` atau `TUGAS SELESAI`. "
                f"Saya akan menunggu respons Anda."
            )

            response = self._get_llm_response(execution_prompt)

            if not response or not response.candidates or not response.candidates[0].content:
                log_error(f"Gagal mendapatkan respons dari AI. Mengakhiri sesi.")
                break

            final_text = " ".join([p.text for p in response.candidates[0].content.parts if p.text]).strip()

            if final_text:
                log_agent_response(final_text)
                if "TUGAS SELESAI" in final_text.upper():
                    log_success(f"--- Tugas Selesai Dikerjakan oleh Agent ---")
                    break
                elif "[LANJUTKAN]" in final_text.upper():
                    log_system_message(f"[Han Agent: Menerima sinyal Lanjutkan. Melanjutkan iterasi...]")
                    plan_text = final_text.replace("[LANJUTKAN]", "").strip() 
                    continue
                else:
                    log_system_message(f"[Han Agent: Respon tidak menandakan Lanjutkan atau Selesai. Sesi ini berakhir untuk menunggu input berikutnya.]")
                    break
            else:
                log_system_message(f"[Han Agent: Respon tidak jelas. Tidak ada panggilan fungsi atau teks. Mengakhiri sesi untuk menghindari loop tak terbatas.]")
                break
        else:
            log_error(f"Mencapai batas iterasi ({MAX_ITERATIONS}). Tugas mungkin belum selesai.")
        log_system_message(f"--- Eksekusi Selesai ---")