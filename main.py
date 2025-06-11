import os
from dotenv import load_dotenv
from agent_core.agent import Agent
from config import DIREKTORI_BATASAN_AI
from utils.colors import Colors
from utils.path_utils import create_workspace_if_not_exists, clean_workspace
from logging_handler import log_user_input, log_agent_response, log_system_message, log_error, log_success

def main():
    load_dotenv()
    create_workspace_if_not_exists()
    clean_prompt = input(f"{Colors.YELLOW}Apakah Anda ingin membersihkan workspace sebelumnya? (y/n): {Colors.RESET}").strip().lower()
    if clean_prompt == 'y':
        clean_workspace()
    else:
        log_system_message("Workspace tidak dibersihkan, melanjutkan sesi sebelumnya.")

    log_system_message(f"\n")
    log_system_message(f"{Colors.BLUE}{'-' * 50}{Colors.RESET}")
    log_system_message(f"{Colors.BOLD}{Colors.BLUE}Selamat datang di HanAgent v2.2.0!{Colors.RESET}")
    log_system_message(f"{Colors.BLUE}HanAgent ini didesain untuk secara iteratif membangun, menguji, dan melakukan debugging kode.{Colors.RESET}")
    log_system_message(f"{Colors.BLUE}Credit: HanSoBored.{Colors.RESET}")
    log_system_message(f"{Colors.BLUE}Ketik '{Colors.BOLD}exit{Colors.RESET}{Colors.BLUE}' untuk keluar.{Colors.RESET}")
    log_system_message(f"{Colors.BLUE}{'-' * 50}{Colors.RESET}\n")

    agent = Agent()
    log_system_message(f"Han Agent siap menerima perintah Anda.")

    while True:
        user_input = input(f"{Colors.BOLD}{Colors.YELLOW}Anda: {Colors.RESET}").strip()
        if user_input.lower() == 'exit':
            log_system_message(f"Keluar dari Han Agent. Sampai jumpa!")
            break

        agent.run_task(user_input)

if __name__ == "__main__":
    main()