import google.generativeai as genai
import google.ai.generativelanguage as glm
from dotenv import load_dotenv
import time
import os
import json

from config import GEMINI_MODEL_NAME, TOOL_CALL_PAUSE_SECONDS, PROMPT_DIRECTORY, SHOW_AGENT_THOUGHTS, SHOW_DEBUG_MESSAGES, DIREKTORI_BATASAN_AI
from logging_handler import log_agent_thought, log_agent_response, log_tool_call, log_tool_output, log_error, log_system_message, log_debug, log_success, log_user_input
from utils.colors import Colors
from tools.file_system_tools import file_system_tool_definitions, file_system_functions
from tools.execution_tools import execution_tool_definitions, execution_functions
from tools.control_tools import control_tool_definitions, control_functions, USER_INPUT_REQUIRED
from tools.internet_tools import internet_tool_definitions, internet_functions
from tools.advanced_tools import advanced_tool_definitions, advanced_functions

load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

MAX_RETRIES_PER_STEP = 2

class Agent:
    def __init__(self):
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
            **file_system_functions, **execution_functions, **control_functions,
            **internet_functions, **advanced_functions
        }

        planner_instruction = self._load_specific_instructions(['_planner_instructions.txt'])
        self.planner_model = genai.GenerativeModel(GEMINI_MODEL_NAME, system_instruction=planner_instruction)

        executor_files = [
            '_base_instructions.txt', '_cli_tool_usage.txt',
            '_general_problem_solving.txt', '_interactive_cli_guide.txt'
        ]
        executor_instruction = self._load_specific_instructions(executor_files)
        executor_instruction += f"\n\n[PENTING] Direktori kerja absolut Anda saat ini adalah: {os.path.abspath(DIREKTORI_BATASAN_AI)}. Semua path relatif harus dari direktori ini."
        
        self.executor_model = genai.GenerativeModel(
            GEMINI_MODEL_NAME,
            tools=[self.all_tool_definitions],
            system_instruction=executor_instruction
        )
        
        validator_instruction = self._load_specific_instructions(['_validator_instructions.txt'])
        self.validator_model = genai.GenerativeModel(GEMINI_MODEL_NAME, system_instruction=validator_instruction)
        
        self.history = []

    def _load_specific_instructions(self, filenames):
        all_instructions = []
        try:
            for filename in filenames:
                filepath = os.path.join(PROMPT_DIRECTORY, filename)
                if os.path.exists(filepath):
                    with open(filepath, 'r', encoding='utf-8') as f:
                        all_instructions.append(f.read())
                    log_debug(f"Memuat instruksi dari: {filename}")
                else:
                    log_error(f"File instruksi tidak ditemukan: {filename}")
            if not all_instructions:
                return "Anda adalah AI yang cerdas."
            return "\n\n".join(all_instructions)
        except Exception as e:
            log_error(f"Gagal memuat instruksi sistem dari file: {e}")
            return "Anda adalah AI yang cerdas."

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

            return glm.Part(function_response=glm.FunctionResponse(name=function_name, response={"result": function_output_json}))
        except Exception as e:
            error_message = f"Gagal mengeksekusi fungsi {function_name}: {e}"
            log_error(error_message)
            error_json = json.dumps({"success": False, "data": error_message})
            return glm.Part(function_response=glm.FunctionResponse(name=function_name, response={"error": error_json}))

    def _invoke_planner(self, user_task):
        prompt = (f"Pengguna memberikan tugas berikut. Buat rencana langkah-demi-langkah yang terperinci dalam format checklist Markdown. Tugas: \"{user_task}\"")
        try:
            response = self.planner_model.generate_content(prompt)
            plan_text = response.text.strip()

            # Memastikan respons perencana adalah checklist Markdown
            if not plan_text.strip().startswith('[ ]'):
                 # Menghapus blok kode markdown jika ada
                if "```markdown" in plan_text:
                    plan_text = plan_text.split("```markdown\n", 1)[1]
                if "```" in plan_text:
                    plan_text = plan_text.rsplit("\n```", 1)[0]

            return plan_text.strip()
        except ValueError as e:
            log_error(f"Gagal mem-parsing rencana dari Agen Perencana: {e}\nRespons mentah: {plan_text}")
            return None
        except Exception as e:
            log_error(f"Terjadi kesalahan saat memanggil Agen Perencana: {e}")
            return None

    def _invoke_validator(self, original_task, current_step, execution_history_slice):
        log_system_message("Memanggil Agen Validasi untuk memeriksa hasil...")

        context_parts = []
        for msg in execution_history_slice:
            role = msg.role
            for part in msg.parts:
                content = ""
                if part.text:
                    content = part.text
                elif part.function_call:
                    args_str = ", ".join(f"{k}={v}" for k, v in part.function_call.args.items())
                    content = f"Tool Call: {part.function_call.name}({args_str})"
                elif part.function_response:
                     content = f"Tool Response for {part.function_response.name}: {part.function_response.response}"
                context_parts.append(f"[{role}] {content}")
        context_text = "\n".join(context_parts)

        prompt = (
            "Anda adalah Agen Validasi. Analisis eksekusi berikut.\n\n"
            f"**TUGAS UTAMA:**\n{original_task}\n\n"
            f"**LANGKAH YANG DIKERJAKAN:**\n{current_step}\n\n"
            f"**LOG EKSEKUSI (Panggilan & Hasil Tool):**\n{context_text}\n\n"
            "Berdasarkan informasi ini, berikan evaluasi Anda dalam format JSON yang telah ditentukan."
        )

        try:
            response = self.validator_model.generate_content(prompt, request_options={"timeout": 90})
            validation_text = response.text.strip()
            
            json_start = validation_text.find('{')
            json_end = validation_text.rfind('}') + 1
            if json_start == -1 or json_end == 0:
                raise ValueError("Tidak ada JSON yang ditemukan dalam respons validator.")
            
            validation_json_str = validation_text[json_start:json_end]
            validation_data = json.loads(validation_json_str)

            if not all(k in validation_data for k in ["is_successful", "reasoning", "suggestion"]):
                 raise ValueError("Format JSON dari validator tidak valid. Harus memiliki kunci 'is_successful', 'reasoning', dan 'suggestion'.")

            return validation_data
        except (json.JSONDecodeError, ValueError) as e:
            log_error(f"Gagal mem-parsing hasil dari Agen Validasi: {e}\nRespons mentah: {validation_text}")
            return {"is_successful": False, "reasoning": "Gagal mem-parsing respons dari validator.", "suggestion": "Coba ulangi langkahnya."}
        except Exception as e:
            log_error(f"Terjadi kesalahan saat memanggil Agen Validasi: {e}")
            return {"is_successful": False, "reasoning": f"Error internal saat validasi: {e}", "suggestion": "Coba ulangi langkahnya."}

    def _invoke_executor(self, prompt):
        self.history.append(glm.Content(role="user", parts=[glm.Part(text=prompt)]))
        
        try:
            response = self.executor_model.generate_content(self.history, request_options={"timeout": 120})
            self.history.append(response.candidates[0].content)

            if SHOW_AGENT_THOUGHTS:
                thought_text = " ".join([p.text for p in response.candidates[0].content.parts if p.text]).strip()
                if thought_text: log_agent_thought(f"Pemikiran:\n{thought_text}")

            while response.candidates and response.candidates[0].content and any(part.function_call for part in response.candidates[0].content.parts):
                tool_calls = [part.function_call for part in response.candidates[0].content.parts if part.function_call]
                
                tool_responses_parts = []
                for call in tool_calls:
                    response_part = self._execute_tool_call(call)
                    tool_responses_parts.append(response_part)
                    time.sleep(TOOL_CALL_PAUSE_SECONDS)
                
                if globals().get('USER_INPUT_REQUIRED'):
                    return 

                self.history.append(glm.Content(role="tool", parts=tool_responses_parts))
                response = self.executor_model.generate_content(self.history, request_options={"timeout": 120})
                self.history.append(response.candidates[0].content)

                if SHOW_AGENT_THOUGHTS:
                    thought_text = " ".join([p.text for p in response.candidates[0].content.parts if p.text]).strip()
                    if thought_text: log_agent_thought(f"Pemikiran setelah tool call:\n{thought_text}")

            return response
        except genai.types.BlockedPromptException as e:
            log_error(f"Permintaan Anda diblokir karena alasan keamanan. Detail: {e}")
            return None
        except Exception as e:
            log_error(f"Terjadi kesalahan saat berkomunikasi dengan model eksekutor: {e}")
            return None

    def _was_signal_tool_called(self, signal_name):
        if not self.history: return False
        for message in reversed(self.history):
            if message.role == 'user': return False
            if message.role == 'model':
                for part in message.parts:
                    if part.function_call and part.function_call.name == signal_name:
                        return True
        return False

    def _find_next_task(self, todo_content: str):
        """Mencari tugas pertama yang belum selesai ([ ]) dari konten todo.md."""
        for line in todo_content.splitlines():
            if line.strip().startswith('[ ]'):
                # Mengembalikan teks tugas setelah '[ ] '
                return line.strip()[4:]
        return None

    def _mark_task_as_done(self, task: str, todo_content: str):
        """Menandai tugas sebagai selesai dengan mengganti '[ ]' menjadi '[x]'."""
        lines = todo_content.splitlines()
        for i, line in enumerate(lines):
            if line.strip().startswith('[ ]') and line.strip()[4:] == task:
                lines[i] = line.replace('[ ]', '[x]', 1)
                log_system_message(f"Tugas '{task}' ditandai selesai di todo.md.")
                return "\n".join(lines)
        return todo_content # Kembalikan konten asli jika tidak ada yang cocok

    def run_task(self, user_task):
        self.history = []
        log_system_message("Memanggil Agen Perencana untuk membuat rencana...")
        plan = self._invoke_planner(user_task)

        if not plan:
            log_error("Agen Perencana gagal membuat rencana. Eksekusi dihentikan.")
            return
        
        log_success("Rencana berhasil dibuat oleh Agen Perencana:")
        try:
            # Membersihkan todo.md dari sisa sesi sebelumnya
            self.available_functions['write_file'](filename='todo.md', content=plan)
            print(plan)
            log_system_message("Rencana telah disimpan ke 'todo.md'")
        except Exception as e:
            log_error(f"Gagal menyimpan rencana ke todo.md: {e}")

        self.history.append(glm.Content(role="user", parts=[glm.Part(text=f"Tugas awal saya: '{user_task}'")]))
        self.history.append(glm.Content(role="model", parts=[glm.Part(text=f"Baik, saya telah membuat rencana dalam `todo.md` dan akan melaksanakannya.")]))

        while True:
            todo_content_json = self.available_functions['read_file'](filename='todo.md')
            todo_content_data = json.loads(todo_content_json)
            if not todo_content_data.get('success'):
                log_error("Gagal membaca todo.md, eksekusi dihentikan.")
                return
            
            todo_content = todo_content_data['data']
            step = self._find_next_task(todo_content)

            if step is None:
                log_success("Semua tugas di todo.md telah selesai.")
                break

            log_system_message(f"--- Memulai Tugas Berikutnya: {step} ---")

            retry_count = 0
            while retry_count <= MAX_RETRIES_PER_STEP:
                history_before_step = len(self.history)

                executor_prompt = ""
                if retry_count > 0:
                     executor_prompt = "Eksekusi sebelumnya gagal validasi. Harap perhatikan umpan balik dalam histori dan coba lagi untuk menyelesaikan langkah saat ini dengan benar."
                else:
                    executor_prompt = (
                        f"Konteks: Tugas utama adalah '{user_task}'.\n\n"
                        f"Fokus HANYA pada penyelesaian tugas dari todo.md ini: \"{step}\".\n\n"
                        "Gunakan tool yang diperlukan, periksa hasilnya, dan laporkan kembali. Jika Anda butuh klarifikasi, gunakan `ask_user_for_input`. "
                        "Jika langkah ini adalah langkah terakhir dan tugas utama telah tercapai, panggil `signal_task_complete`."
                    )
                
                self._invoke_executor(executor_prompt)
                
                if globals().get('USER_INPUT_REQUIRED'):
                    user_input_text = input(f"{Colors.BOLD}{Colors.GREEN}Input Anda: {Colors.RESET}").strip()
                    log_user_input(user_input_text)
                    globals()['USER_INPUT_REQUIRED'] = False
                    
                    user_feedback_part = glm.Part(function_response=glm.FunctionResponse(name="ask_user_for_input", response={"result": json.dumps({"success": True, "data": f"Pengguna merespons: {user_input_text}"})}))
                    self.history.append(glm.Content(role="tool", parts=[user_feedback_part]))

                    log_system_message("Melanjutkan eksekusi langkah saat ini dengan input dari pengguna...")
                    self._invoke_executor("Terima kasih atas inputnya. Lanjutkan eksekusi langkah saat ini berdasarkan informasi baru tersebut.")

                if self._was_signal_tool_called("signal_task_complete"):
                    break 

                history_for_validation = self.history[history_before_step:]
                validation_result = self._invoke_validator(user_task, step, history_for_validation)

                if validation_result["is_successful"]:
                    log_success(f"VALIDASI BERHASIL: {validation_result['reasoning']}")
                    # Tandai tugas sebagai selesai di todo.md
                    updated_todo_content = self._mark_task_as_done(step, todo_content)
                    self.available_functions['write_file'](filename='todo.md', content=updated_todo_content)

                    break 
                else:
                    retry_count += 1
                    log_error(f"VALIDASI GAGAL (Percobaan {retry_count}/{MAX_RETRIES_PER_STEP}): {validation_result['reasoning']}")
                    log_system_message(f"Saran perbaikan dari Validator: {validation_result['suggestion']}")
                    
                    if retry_count > MAX_RETRIES_PER_STEP:
                        log_error("Jumlah maksimum percobaan ulang untuk langkah ini tercapai. Menghentikan eksekusi.")
                        return 
                    
                    feedback_for_executor = (
                        f"Pemeriksaan oleh Agen Validasi menemukan masalah. "
                        f"Alasan: {validation_result['reasoning']}. "
                        f"Saran untuk perbaikan: {validation_result['suggestion']}. "
                        "Silakan coba lagi untuk menyelesaikan langkah ini dengan benar."
                    )
                    self.history.append(glm.Content(role="user", parts=[glm.Part(text=feedback_for_executor)]))

            if self._was_signal_tool_called("signal_task_complete"):
                break

        if self._was_signal_tool_called("signal_task_complete"):
            log_success("--- TUGAS SELESAI DIKERJAKAN (menurut sinyal AI) ---")
            final_summary = "AI tidak memberikan ringkasan."
            try:
                for msg in reversed(self.history):
                    if msg.role == 'model':
                        for part in msg.parts:
                            if part.function_call and part.function_call.name == "signal_task_complete":
                                final_summary = part.function_call.args.get('final_summary', 'Tidak ada ringkasan yang diberikan.')
                                break
                        if final_summary != "AI tidak memberikan ringkasan.": break
            except Exception as e:
                log_debug(f"Tidak dapat mengekstrak ringkasan akhir: {e}")
            
            log_agent_response(f"Ringkasan Akhir dari AI:\n{final_summary}")
        elif step is None: # Loop selesai secara alami
             log_success("--- TUGAS SELESAI DIKERJAKAN (semua item todo.md dicentang) ---")

        log_system_message(f"--- Sesi Eksekusi Selesai ---")