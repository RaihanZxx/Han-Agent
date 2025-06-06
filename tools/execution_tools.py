import subprocess
import shlex
import google.ai.generativelanguage as glm
from google.ai.generativelanguage import Type
import os

from utils.path_utils import sanitize_path
from config import DIREKTORI_BATASAN_AI

def shlex_join(args_list):
    return shlex.join(args_list)

def execute_command(command, args=None, timeout=60):
    if args is None:
        args = []

    allowed_commands = [
        'python3', 'python', 'ls', 'cat', 'echo', 'pip3', 'pip',
        'chmod', 'git', 'npm', 'node', 'sh', 'bash', 'find', 'grep',
        'mkdir', 'rm', 'cp', 'mv',
        'make', 'gcc', 'g++', 'clang', 'cmake',
        'java', 'javac', 'jar', 'jarsigner', 'keytool',
        'adb', 'fastboot',
        'aapt', 'aapt2', 'apksigner', 'zipalign', 'd8', 'dx',
        'gradle', 'mvn',
        'unzip', 'tar',
        'apktool'
    ]

    if ' ' in command and len(args) > 0:
        return f"Kesalahan keamanan: Perintah '{command}' tidak boleh mengandung spasi jika argumen diberikan secara terpisah. " \
               f"AI harus memanggil fungsi dengan 'command' hanya nama perintah (misal: 'python3') dan 'args' sebagai daftar (misal: ['script.py'])."

    if command not in allowed_commands:
        return f"Kesalahan keamanan: Perintah '{command}' tidak diizinkan. " \
               f"Perintah yang diizinkan: {', '.join(allowed_commands)}"

    full_command = [str(command)] + [str(arg) for arg in args]

    try:
        result = subprocess.run(
            full_command,
            cwd=DIREKTORI_BATASAN_AI,
            capture_output=True,
            text=True,
            check=False,
            shell=False,
            timeout=timeout
        )

        output = f"Output STDOUT:\n{result.stdout}\n"
        if result.stderr:
            output += f"Output STDERR:\n{result.stderr}\n"
        output += f"Exit Code: {result.returncode}"

        return output
    except FileNotFoundError:
        return f"Error: Perintah '{command}' tidak ditemukan. Pastikan terinstal dan ada di PATH (dan tersedia di sandbox AI)."
    except subprocess.TimeoutExpired:
        return f"Error: Perintah '{shlex_join(full_command)}' melebihi batas waktu {timeout} detik."
    except Exception as e:
        return f"Gagal mengeksekusi perintah '{shlex_join(full_command)}': {e}"

def install_python_package(package_name):
    try:
        output_pip3 = execute_command('pip3', ['install', package_name])
        if "Exit Code: 0" in output_pip3 and "Could not find a version that satisfies the requirement" not in output_pip3:
            return f"Paket '{package_name}' berhasil diinstal:\n{output_pip3}"
        else:
            output_pip = execute_command('pip', ['install', package_name])
            if "Exit Code: 0" in output_pip and "Could not find a version that satisfies the requirement" not in output_pip:
                return f"Paket '{package_name}' berhasil diinstal (menggunakan pip):\n{output_pip}"
            else:
                return f"Gagal menginstal paket '{package_name}':\nOutput pip3:\n{output_pip3}\nOutput pip:\n{output_pip}"
    except Exception as e:
        return f"Terjadi kesalahan saat mencoba menginstal paket '{package_name}': {e}"

def set_permissions(path, mode):
    try:
        full_path = sanitize_path(path)
        if not isinstance(mode, str) or not mode.isdigit() or not (1 <= len(mode) <= 4):
            return f"Error: Mode harus berupa string digit oktal (contoh: '755', '644')."

        os.chmod(full_path, int(mode, 8))
        return f"Izin untuk '{path}' berhasil diatur ke {mode}."
    except ValueError as e:
        return f"Kesalahan keamanan: {e}"
    except FileNotFoundError:
        return f"Jalur '{path}' tidak ditemukan."
    except Exception as e:
        return f"Gagal mengatur izin untuk '{path}': {e}"

execution_tool_definitions = glm.Tool(
    function_declarations=[
        glm.FunctionDeclaration(
            name="execute_command",
            description="Mengeksekusi perintah command line di dalam lingkungan sandbox AI. "
                        "Hanya perintah yang diizinkan (misalnya 'python3', 'ls', 'make', 'git', 'adb', 'aapt2', 'gradle' dll.) "
                        "dapat dijalankan. Ini memungkinkan AI untuk menjalankan skrip, melihat isi file, "
                        "atau membuat/mengubah izin direktori dengan perintah shell dasar, serta melakukan kompilasi. "
                        "Output stdout dan stderr akan dikembalikan, bersama dengan exit code. "
                        "Gunakan ini untuk menjalankan skrip Python yang Anda buat atau untuk debugging. "
                        "Penting: 'command' haruslah nama perintah tunggal (contoh: 'python3', 'ls'), "
                        "dan semua argumen harus diteruskan sebagai daftar string di parameter 'args' "
                        "(contoh: args=['script.py', '--verbose']). Jangan pernah masukkan argumen ke dalam parameter 'command'.",
            parameters=glm.Schema(
                type=Type.OBJECT,
                properties={
                    "command": glm.Schema(type=Type.STRING, description="Perintah yang akan dijalankan (misal: 'python3', 'ls')."),
                    "args": glm.Schema(type=Type.ARRAY, items=glm.Schema(type=Type.STRING), description="Daftar argumen untuk perintah. (misal: ['script.py', '--help'])."),
                    "timeout": glm.Schema(type=Type.NUMBER, description="Batas waktu eksekusi perintah dalam detik (default: 60).")
                },
                required=["command"]
            )
        ),
        glm.FunctionDeclaration(
            name="install_python_package",
            description="Menginstal paket Python menggunakan pip di dalam lingkungan AI. "
                        "Gunakan ini jika skrip Python yang Anda buat membutuhkan modul eksternal.",
            parameters=glm.Schema(
                type=Type.OBJECT,
                properties={
                    "package_name": glm.Schema(type=Type.STRING, description="Nama paket Python yang akan diinstal (misal: 'requests', 'numpy').")
                },
                required=["package_name"]
            )
        ),
        glm.FunctionDeclaration(
            name="set_permissions",
            description="Mengubah izin file atau direktori di lingkungan AI. "
                        "Berguna untuk membuat skrip dapat dieksekusi atau mengatur izin folder. "
                        "Mode harus dalam format oktal (misal: '755' untuk rwxr-xr-x).",
            parameters=glm.Schema(
                type=Type.OBJECT,
                properties={
                    "path": glm.Schema(type=Type.STRING, description="Jalur file atau direktori yang akan diubah izinnya."),
                    "mode": glm.Schema(type=Type.STRING, description="Mode izin oktal (misal: '755').")
                },
                required=["path", "mode"]
            )
        )
    ]
)

execution_functions = {
    "execute_command": execute_command,
    "install_python_package": install_python_package,
    "set_permissions": set_permissions,
}