import google.generativeai as genai
import google.ai.generativelanguage as glm
from dotenv import load_dotenv
import time
import os
import json
from google.protobuf import struct_pb2
from google.protobuf.json_format import MessageToDict, ParseDict

from config import (
    GEMINI_MODEL_NAME,
    TOOL_CALL_PAUSE_SECONDS,
    PROMPT_DIRECTORY,
    SHOW_AGENT_THOUGHTS,
    DIREKTORI_BATASAN_AI,
    MEMORY_FILE_NAME,
)
from logging_handler import (
    log_agent_thought,
    log_agent_response,
    log_tool_call,
    log_tool_output,
    log_error,
    log_system_message,
    log_debug,
)
from utils.colors import Colors
from tools.file_system_tools import file_system_tool_definitions, file_system_functions
from tools.execution_tools import execution_tool_definitions, execution_functions
from tools.control_tools import control_tool_definitions, control_functions
from tools.internet_tools import internet_tool_definitions, internet_functions
from tools.advanced_tools import advanced_tool_definitions, advanced_functions
from tools.todo_manager_tools import todo_manager_tool_definitions, todo_manager_functions

load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

class Agent:
    def __init__(self):
        # Menggabungkan semua definisi tool yang tersedia
        self.all_tool_definitions = glm.Tool(
            function_declarations=(
                list(file_system_tool_definitions.function_declarations)
                + list(execution_tool_definitions.function_declarations)
                + list(control_tool_definitions.function_declarations)
                + list(internet_tool_definitions.function_declarations)
                + list(advanced_tool_definitions.function_declarations)
                + list(todo_manager_tool_definitions.function_declarations)
            )
        )
        # Menggabungkan semua fungsi tool yang tersedia
        self.available_functions = {
            **file_system_functions,
            **execution_functions,
            **control_functions,
            **internet_functions,
            **advanced_functions,
            **todo_manager_functions,
        }

        # Memuat instruksi sistem dasar untuk agen percakapan
        system_instruction_files = [
            "_planner_instructions.txt",
            "_validator_instructions.txt",
            "kernelsu_webui_backend_guide.txt",
        ]
        system_instruction = self._load_specific_instructions(system_instruction_files)
        system_instruction += f"\n\n[PENTING] Direktori kerja absolut Anda saat ini adalah: {os.path.abspath(DIREKTORI_BATASAN_AI)}. Semua path relatif harus dari direktori ini."

        # Inisialisasi model generatif utama
        self.model = genai.GenerativeModel(
            GEMINI_MODEL_NAME,
            tools=[self.all_tool_definitions],
            system_instruction=system_instruction,
        )

        # Memuat riwayat percakapan untuk memulai sesi chat yang stateful
        loaded_history = self._load_history()
        self.chat = self.model.start_chat(history=loaded_history)
        log_system_message("Agen percakapan stateful telah dimulai.")

    def _to_dict_recursive(self, obj):
        if isinstance(obj, dict):
            return {k: self._to_dict_recursive(v) for k, v in obj.items()}
        elif hasattr(obj, 'items') and callable(getattr(obj, 'items')):
            # This handles MapComposite and similar
            return {k: self._to_dict_recursive(v) for k, v in obj.items()}
        elif hasattr(obj, 'DESCRIPTOR') and hasattr(obj, 'ListFields'):
            # This handles protobuf messages
            return MessageToDict(obj)
        elif isinstance(obj, list) or (hasattr(obj, '__iter__') and not isinstance(obj, str)):
            # This handles lists and RepeatedComposite
            return [self._to_dict_recursive(elem) for elem in obj]
        else:
            return obj

    def _save_history(self):
        history_data = []
        for message in self.chat.history:
            # Melewatkan pesan sistem atau pesan tanpa konten untuk menjaga kebersihan riwayat
            if not message.parts:
                continue
            parts_data = []
            for part in message.parts:
                part_dict = {}
                if hasattr(part, 'text') and part.text:
                    part_dict["text"] = part.text
                if hasattr(part, 'function_call') and part.function_call:
                    part_dict["function_call"] = {
                        "name": part.function_call.name,
                        "args": self._to_dict_recursive(part.function_call.args),
                    }
                # Hanya menyimpan bagian yang relevan dari function_response
                if hasattr(part, 'function_response') and part.function_response:
                     part_dict["function_response"] = {
                        "name": part.function_response.name,
                        "response": self._to_dict_recursive(part.function_response.response),
                    }
                if part_dict:
                    parts_data.append(part_dict)
            if parts_data:
                 history_data.append({"role": message.role, "parts": parts_data})

        try:
            with open(MEMORY_FILE_NAME, "w", encoding="utf-8") as f:
                json.dump(history_data, f, indent=4)
        except Exception as e:
            log_error(f"Gagal menyimpan riwayat percakapan: {e}")

    def _load_history(self):
        if not os.path.exists(MEMORY_FILE_NAME):
            return []
        try:
            with open(MEMORY_FILE_NAME, "r", encoding="utf-8") as f:
                history_data = json.load(f)

            loaded_history = []
            for message_data in history_data:
                role = message_data.get("role")
                parts_data = message_data.get("parts", [])
                
                if not role or not parts_data:
                    continue

                parts = []
                for part_data in parts_data:
                    if "text" in part_data:
                        parts.append(glm.Part(text=part_data["text"]))
                    elif "function_call" in part_data:
                        fc_data = part_data["function_call"]
                        args_struct = ParseDict(fc_data["args"], struct_pb2.Struct())
                        parts.append(glm.Part(function_call=glm.FunctionCall(name=fc_data["name"], args=args_struct)))
                    elif "function_response" in part_data:
                        fr_data = part_data["function_response"]
                        response_struct = ParseDict(fr_data["response"], struct_pb2.Struct())
                        parts.append(glm.Part(function_response=glm.FunctionResponse(name=fr_data["name"], response=response_struct)))
                
                if parts:
                    loaded_history.append(glm.Content(role=role, parts=parts))
            
            log_debug(f"Riwayat percakapan berhasil dimuat dari {MEMORY_FILE_NAME}")
            return loaded_history
            
        except (Exception) as e:
            log_error(f"Gagal memuat atau mem-parsing riwayat percakapan: {e}")
            # Jika file rusak, mulai dengan riwayat kosong
            if os.path.exists(MEMORY_FILE_NAME):
                try:
                    os.rename(MEMORY_FILE_NAME, f"{MEMORY_FILE_NAME}.corrupt")
                    log_error(f"File riwayat yang rusak diganti nama menjadi {MEMORY_FILE_NAME}.corrupt")
                except OSError as ose:
                    log_error(f"Gagal mengganti nama file riwayat yang rusak: {ose}")
            return []

    def _load_specific_instructions(self, filenames):
        all_instructions = []
        try:
            for filename in filenames:
                filepath = os.path.join(PROMPT_DIRECTORY, filename)
                if os.path.exists(filepath):
                    with open(filepath, "r", encoding="utf-8") as f:
                        all_instructions.append(f.read())
                else:
                    log_error(f"File instruksi tidak ditemukan: {filename}")
            return "\n\n".join(all_instructions) if all_instructions else "Anda adalah AI yang cerdas."
        except Exception as e:
            log_error(f"Gagal memuat instruksi sistem: {e}")
            return "Anda adalah AI yang cerdas."

    def _execute_tool_call(self, tool_call):
        function_name = tool_call.name
        function_args = {k: v for k, v in tool_call.args.items()}
        log_tool_call(function_name, function_args)

        try:
            # Memanggil fungsi tool yang sesuai
            function_output = self.available_functions[function_name](**function_args)
            log_tool_output(function_name, function_output)
            
            # Mengemas output ke dalam format yang diharapkan oleh model
            return glm.Part(
                function_response=glm.FunctionResponse(
                    name=function_name, response=ParseDict({"result": function_output}, struct_pb2.Struct())
                )
            )
        except Exception as e:
            error_message = f"Gagal mengeksekusi fungsi {function_name}: {e}"
            log_error(error_message)
            return glm.Part(
                function_response=glm.FunctionResponse(
                    name=function_name, response=ParseDict({"error": error_message}, struct_pb2.Struct())
                )
            )

    def interact(self, user_input):
        try:
            # Mengirim pesan pengguna ke sesi chat yang stateful
            response = self.chat.send_message(user_input)

            while True:
                # Memeriksa apakah model meminta pemanggilan tool
                if response.candidates and response.candidates[0].content.parts and response.candidates[0].content.parts[0].function_call:
                    tool_calls = [part.function_call for part in response.candidates[0].content.parts]
                    
                    if SHOW_AGENT_THOUGHTS:
                        log_agent_thought("Memutuskan untuk menggunakan tool...")

                    tool_responses = []
                    for call in tool_calls:
                        # Mengeksekusi setiap tool call
                        response_part = self._execute_tool_call(call)
                        tool_responses.append(response_part)
                        time.sleep(TOOL_CALL_PAUSE_SECONDS)
                    
                    # Mengirim hasil eksekusi tool kembali ke model
                    response = self.chat.send_message(tool_responses)
                else:
                    # Jika tidak ada lagi tool call, loop selesai
                    break
            
            # Mengambil dan menampilkan respons teks akhir dari AI
            final_text_response = " ".join([part.text for part in response.candidates[0].content.parts if part.text]).strip()
            if final_text_response:
                log_agent_response(final_text_response)
            else:
                log_system_message("Tugas selesai tanpa output teks.")

            # Menyimpan riwayat setelah setiap interaksi yang berhasil
            self._save_history()

        except Exception as e:
            log_error(f"Terjadi kesalahan besar saat interaksi: {e}")
