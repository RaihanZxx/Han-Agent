import subprocess
import shlex
import google.ai.generativelanguage as glm
from google.ai.generativelanguage import Type
import os
import json

from utils.path_utils import sanitize_path
from config import DIREKTORI_BATASAN_AI

def shlex_join(args_list):
    return shlex.join(args_list)

def execute_command(command, args=None, timeout=60):
    if args is None:
        args = []

    if ' ' in command and len(args) > 0:
        error_msg = f"Kesalahan keamanan: Perintah '{command}' tidak boleh mengandung spasi jika argumen diberikan secara terpisah. Panggil dengan 'command' hanya nama perintah dan 'args' sebagai daftar."
        return json.dumps({"success": False, "data": error_msg})

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

        output_data = {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode
        }
        
        success = result.returncode == 0
        return json.dumps({"success": success, "data": output_data})

    except FileNotFoundError:
        error_msg = f"Error: Perintah '{command}' tidak ditemukan. Pastikan program terinstal dan berada di dalam PATH sistem, atau gunakan path absolut."
        return json.dumps({"success": False, "data": error_msg})
    except subprocess.TimeoutExpired:
        return json.dumps({"success": False, "data": f"Error: Perintah '{shlex_join(full_command)}' melebihi batas waktu {timeout} detik."})
    except Exception as e:
        return json.dumps({"success": False, "data": f"Gagal mengeksekusi perintah '{shlex_join(full_command)}': {e}"})

def install_python_package(package_name):
    try:
        pip3_result_json = execute_command('pip3', ['install', package_name])
        pip3_result = json.loads(pip3_result_json)

        if pip3_result['success']:
            return json.dumps({"success": True, "data": f"Paket '{package_name}' berhasil diinstal menggunakan pip3. Output: {pip3_result['data']}"})

        pip_result_json = execute_command('pip', ['install', package_name])
        pip_result = json.loads(pip_result_json)

        if pip_result['success']:
            return json.dumps({"success": True, "data": f"Paket '{package_name}' berhasil diinstal menggunakan pip. Output: {pip_result['data']}"})
        
        return json.dumps({"success": False, "data": f"Gagal menginstal paket '{package_name}'.\nOutput pip3: {pip3_result['data']}\nOutput pip: {pip_result['data']}"})

    except Exception as e:
        return json.dumps({"success": False, "data": f"Terjadi kesalahan saat mencoba menginstal paket '{package_name}': {e}"})

def set_permissions(path, mode):
    try:
        full_path = sanitize_path(path)
        if not isinstance(mode, str) or not mode.isdigit() or not (1 <= len(mode) <= 4):
            return json.dumps({"success": False, "data": "Error: Mode harus berupa string digit oktal (contoh: '755', '644')."})

        os.chmod(full_path, int(mode, 8))
        return json.dumps({"success": True, "data": f"Izin untuk '{path}' berhasil diatur ke {mode}."})
    except ValueError as e:
        return json.dumps({"success": False, "data": f"Kesalahan keamanan: {e}"})
    except FileNotFoundError:
        return json.dumps({"success": False, "data": f"Jalur '{path}' tidak ditemukan."})
    except Exception as e:
        return json.dumps({"success": False, "data": f"Gagal mengatur izin untuk '{path}': {e}"})

execution_tool_definitions = glm.Tool(
    function_declarations=[
        glm.FunctionDeclaration(
            name="execute_command",
            description="Mengeksekusi perintah command line. Mengembalikan objek JSON dengan kunci 'success' (boolean), dan 'data' yang berisi 'stdout', 'stderr', dan 'exit_code'. 'success' bernilai true jika exit_code adalah 0.",
            parameters=glm.Schema(type=Type.OBJECT, properties={"command": glm.Schema(type=Type.STRING), "args": glm.Schema(type=Type.ARRAY, items=glm.Schema(type=Type.STRING)), "timeout": glm.Schema(type=Type.NUMBER)}, required=["command"])
        ),
        glm.FunctionDeclaration(
            name="install_python_package",
            description="Menginstal paket Python menggunakan pip. Mengembalikan JSON dengan status keberhasilan.",
            parameters=glm.Schema(type=Type.OBJECT, properties={"package_name": glm.Schema(type=Type.STRING)}, required=["package_name"])
        ),
        glm.FunctionDeclaration(
            name="set_permissions",
            description="Mengubah izin file atau direktori. Mengembalikan JSON dengan status keberhasilan.",
            parameters=glm.Schema(type=Type.OBJECT, properties={"path": glm.Schema(type=Type.STRING), "mode": glm.Schema(type=Type.STRING)}, required=["path", "mode"])
        )
    ]
)

execution_functions = {
    "execute_command": execute_command,
    "install_python_package": install_python_package,
    "set_permissions": set_permissions,
}