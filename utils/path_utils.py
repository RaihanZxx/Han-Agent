import os
import shutil
from config import DIREKTORI_BATASAN_AI
from utils.colors import Colors
from logging_handler import log_system_message, log_error, log_success


def sanitize_path(filepath):
    abs_base_path = os.path.abspath(DIREKTORI_BATASAN_AI)

    full_path = os.path.abspath(os.path.join(abs_base_path, filepath))

    if os.path.commonpath([abs_base_path, full_path]) != abs_base_path:
        raise ValueError(
            f"{Colors.RED}Akses ditolak: Mencoba mengakses jalur di luar workspace AI: {filepath}{Colors.RESET}"
        )

    return full_path


def create_workspace_if_not_exists():
    if not os.path.exists(DIREKTORI_BATASAN_AI):
        os.makedirs(DIREKTORI_BATASAN_AI)
        log_success(f"Direktori kerja AI '{DIREKTORI_BATASAN_AI}' telah dibuat.")
    else:
        log_system_message(f"Menggunakan direktori kerja AI: '{DIREKTORI_BATASAN_AI}'")


def clean_workspace():
    log_system_message(f"Membersihkan direktori kerja AI '{DIREKTORI_BATASAN_AI}'...")
    for item in os.listdir(DIREKTORI_BATASAN_AI):
        item_path = os.path.join(DIREKTORI_BATASAN_AI, item)
        try:
            if os.path.isfile(item_path) or os.path.islink(item_path):
                os.unlink(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)
        except Exception as e:
            log_error(f"Gagal membersihkan '{item_path}': {e}")
    log_success(f"Direktori kerja AI '{DIREKTORI_BATASAN_AI}' telah dibersihkan.")
