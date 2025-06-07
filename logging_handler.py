from utils.colors import Colors
import json
import textwrap
import shlex
from config import SHOW_DEBUG_MESSAGES

MAX_TOOL_ARG_LENGTH = 200
MAX_TOOL_OUTPUT_LENGTH = 1000
MAX_FILE_PREVIEW_LINES = 10
MAX_LINES_FOR_TRUNCATION = 20

def _truncate_string(s, max_len):
    if len(s) > max_len:
        return s[:max_len] + f"... (truncated, total {len(s)} chars)"
    return s

def _truncate_lines(s, max_lines):
    lines = s.splitlines()
    if len(lines) > max_lines:
        return "\n".join(lines[:max_lines]) + f"\n... (truncated, total {len(lines)} lines)"
    return s

def log_user_input(text):
    print(f"{Colors.BOLD}{Colors.YELLOW}Anda: {Colors.RESET}{text}")

def log_agent_thought(text):
    print(f"\n{Colors.BLUE}{Colors.BOLD}Han Agent (Memikirkan): {Colors.RESET}")
    print(textwrap.indent(text, prefix="    "))

def log_agent_response(text):
    print(f"{Colors.BOLD}{Colors.BLUE}Han Agent: {Colors.RESET}{text}")
    print()

def log_system_message(message):
    print(f"{Colors.CYAN}[SYSTEM]: {message}{Colors.RESET}")

def log_error(message):
    print(f"{Colors.RED}[ERROR]: {message}{Colors.RESET}")

def log_success(message):
    print(f"{Colors.GREEN}[SUCCESS]: {message}{Colors.RESET}")

def log_debug(message):
    if SHOW_DEBUG_MESSAGES:
        print(f"{Colors.MAGENTA}[DEBUG]: {message}{Colors.RESET}")

def log_tool_call(function_name, args):
    if function_name == 'ask_user_for_input':
        question = args.get('question', '...')
        print(f"\n{Colors.YELLOW}🤔 {Colors.BOLD}Meminta Input Pengguna:{Colors.RESET}")
        print(f"    {question}")
        return

    print(f"\n{Colors.MAGENTA}🧰 {Colors.BOLD}Memanggil Tool:{Colors.RESET} {Colors.MAGENTA}{function_name}{Colors.RESET}")
    if args:
        for key, value in args.items():
            if key == "content" and isinstance(value, str):
                if len(value) > MAX_TOOL_ARG_LENGTH:
                    preview = _truncate_string(value.splitlines()[0], 50) + "..."
                    print(f"    📄 {key}: (panjang {len(value)} karakter, cuplikan: '{preview}')")
                else:
                    lines = value.splitlines()
                    preview_content = "\n".join(lines[:MAX_FILE_PREVIEW_LINES])
                    if len(lines) > MAX_FILE_PREVIEW_LINES:
                        preview_content += f"\n... (total {len(lines)} baris)"
                    print(f"    📝 {key}:\n{textwrap.indent(preview_content, prefix='        ')}")
            elif key == "args" and isinstance(value, list):
                print(f"    ⚙️ {key}: {shlex.join(value)}")
            elif isinstance(value, str) and len(value) > MAX_TOOL_ARG_LENGTH:
                print(f"    🏷️ {key}: {_truncate_string(value, MAX_TOOL_ARG_LENGTH)}")
            else:
                print(f"    🏷️ {key}: {value}")
    else:
        print("    (Tanpa argumen)")

def log_tool_output(function_name, output_result):
    if function_name == 'ask_user_for_input':
        print("-" * 30 + Colors.RESET)
        return
        
    if isinstance(output_result, dict) and "success" in output_result and "data" in output_result:
        success = output_result["success"]
        data = output_result["data"]
        
        if success:
            print(f"{Colors.GREEN}└─ Hasil Sukses dari {function_name}: {Colors.RESET}")
        else:
            print(f"{Colors.RED}└─ Hasil Gagal dari {function_name}: {Colors.RESET}")
        
        if isinstance(data, dict):
            display_data = json.dumps(data, indent=2, ensure_ascii=False)
        elif isinstance(data, list):
            display_data = "\n".join(f"- {item}" for item in data) if data else "(Daftar kosong)"
        else:
            display_data = str(data)
    else:
        print(f"{Colors.YELLOW}└─ Hasil {function_name} (Format tidak standar): {Colors.RESET}")
        display_data = str(output_result)

    formatted_output = _truncate_lines(display_data, MAX_LINES_FOR_TRUNCATION)
    formatted_output = _truncate_string(formatted_output, MAX_TOOL_OUTPUT_LENGTH)
    
    print(textwrap.indent(formatted_output, prefix="    "))
    print("-" * 30 + Colors.RESET)
    
def shlex_join(args_list):
    return shlex.join(args_list)