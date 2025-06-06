from utils.colors import Colors
import json
import textwrap
import shlex

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
    print(f"{Colors.BLUE}{Colors.BOLD}Han Agent (Memikirkan): {Colors.RESET}")
    print(textwrap.indent(text, prefix="    "))
    print()

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
    print(f"{Colors.MAGENTA}[DEBUG]: {message}{Colors.RESET}")

def log_tool_call(function_name, args):
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
                print(f"    ⚙️ {key}: {shlex_join(value)}")
            elif isinstance(value, str) and len(value) > MAX_TOOL_ARG_LENGTH:
                print(f"    🏷️ {key}: {_truncate_string(value, MAX_TOOL_ARG_LENGTH)}")
            else:
                print(f"    🏷️ {key}: {value}")
    else:
        print("    (Tanpa argumen)")

def log_tool_output(function_name, output_result):
    print(f"{Colors.GREEN}└─ Hasil {function_name}: {Colors.RESET}")
    formatted_output = _truncate_lines(str(output_result), MAX_LINES_FOR_TRUNCATION)
    formatted_output = _truncate_string(formatted_output, MAX_TOOL_OUTPUT_LENGTH)
    print(textwrap.indent(formatted_output, prefix="    "))
    print("-" * 30 + Colors.RESET)
    
def shlex_join(args_list):
    return shlex.join(args_list)