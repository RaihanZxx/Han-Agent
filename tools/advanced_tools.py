import google.ai.generativelanguage as glm
from google.ai.generativelanguage import Type
import json
import os
import subprocess
import shlex

from config import DIREKTORI_BATASAN_AI

SCRATCHPAD_FILE = os.path.join(DIREKTORI_BATASAN_AI, ".scratchpad.json")


def _read_scratchpad_data():
    if not os.path.exists(SCRATCHPAD_FILE):
        return {}
    try:
        with open(SCRATCHPAD_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def write_to_scratchpad(key: str, value: str):
    try:
        data = _read_scratchpad_data()
        data[key] = value
        with open(SCRATCHPAD_FILE, "w") as f:
            json.dump(data, f, indent=2)
        return json.dumps(
            {
                "success": True,
                "data": f"Informasi berhasil disimpan dengan kunci '{key}'.",
            }
        )
    except Exception as e:
        return json.dumps(
            {"success": False, "data": f"Gagal menulis ke scratchpad: {e}"}
        )


def read_from_scratchpad(key: str):
    data = _read_scratchpad_data()
    value = data.get(key)
    if value is not None:
        return json.dumps({"success": True, "data": value})
    else:
        return json.dumps(
            {
                "success": False,
                "data": f"Tidak ada informasi yang ditemukan untuk kunci '{key}'.",
            }
        )


BACKGROUND_PROCESSES = {}


def start_background_process(command: str, args: list = None):
    if args is None:
        args = []
    full_command = [str(command)] + [str(arg) for arg in args]
    try:
        process = subprocess.Popen(
            full_command,
            cwd=DIREKTORI_BATASAN_AI,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=False,
        )
        pid = process.pid
        BACKGROUND_PROCESSES[pid] = process
        return json.dumps(
            {
                "success": True,
                "data": {
                    "pid": pid,
                    "message": f"Proses '{shlex.join(full_command)}' dimulai di latar belakang dengan PID {pid}.",
                },
            }
        )
    except Exception as e:
        return json.dumps(
            {"success": False, "data": f"Gagal memulai proses latar belakang: {e}"}
        )


def send_input_to_process(pid: int, input_string: str):
    pid = int(pid)
    if pid not in BACKGROUND_PROCESSES:
        return json.dumps(
            {
                "success": False,
                "data": f"Tidak ada proses latar belakang dengan PID {pid} yang ditemukan.",
            }
        )

    process = BACKGROUND_PROCESSES[pid]
    if process.poll() is not None:
        del BACKGROUND_PROCESSES[pid]
        return json.dumps(
            {
                "success": False,
                "data": f"Proses dengan PID {pid} sudah tidak berjalan lagi.",
            }
        )

    try:
        full_input = (
            input_string if input_string.endswith("\n") else input_string + "\n"
        )
        process.stdin.write(full_input)
        process.stdin.flush()
        return json.dumps(
            {"success": True, "data": f"Input berhasil dikirim ke proses PID {pid}."}
        )
    except Exception as e:
        return json.dumps(
            {"success": False, "data": f"Gagal mengirim input ke proses PID {pid}: {e}"}
        )


def check_process_status(pid: int):
    pid = int(pid)
    if pid not in BACKGROUND_PROCESSES:
        return json.dumps(
            {
                "success": False,
                "data": f"Tidak ada proses latar belakang dengan PID {pid} yang ditemukan.",
            }
        )

    process = BACKGROUND_PROCESSES[pid]
    return_code = process.poll()

    stdout_res = ""
    stderr_res = ""

    response_data = {
        "pid": pid,
        "status": "berjalan" if return_code is None else "selesai",
        "exit_code": return_code,
        "stdout": stdout_res,
        "stderr": stderr_res,
        "note": "Untuk output real-time, periksa file log yang dibuat oleh proses. Tool ini hanya akan menampilkan output lengkap setelah proses selesai.",
    }

    if return_code is not None:
        try:
            stdout_res, stderr_res = process.communicate(timeout=5)
            response_data["stdout"] = stdout_res
            response_data["stderr"] = stderr_res
        except Exception:
            response_data["stdout"] = "(gagal membaca stdout akhir)"
            response_data["stderr"] = "(gagal membaca stderr akhir)"

        del BACKGROUND_PROCESSES[pid]

    return json.dumps({"success": True, "data": response_data})


def stop_process(pid: int):
    pid = int(pid)
    if pid not in BACKGROUND_PROCESSES:
        return json.dumps(
            {
                "success": False,
                "data": f"Tidak ada proses latar belakang dengan PID {pid} untuk dihentikan.",
            }
        )

    try:
        process = BACKGROUND_PROCESSES[pid]
        process.terminate()
        process.wait(timeout=5)
        del BACKGROUND_PROCESSES[pid]
        return json.dumps(
            {"success": True, "data": f"Proses dengan PID {pid} berhasil dihentikan."}
        )
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
        del BACKGROUND_PROCESSES[pid]
        return json.dumps(
            {
                "success": True,
                "data": f"Proses dengan PID {pid} dihentikan secara paksa (kill).",
            }
        )
    except Exception as e:
        if pid not in BACKGROUND_PROCESSES:
            return json.dumps(
                {"success": True, "data": f"Proses PID {pid} sudah tidak berjalan."}
            )
        return json.dumps(
            {"success": False, "data": f"Gagal menghentikan proses PID {pid}: {e}"}
        )


def list_running_processes():
    if not BACKGROUND_PROCESSES:
        return json.dumps(
            {
                "success": True,
                "data": {"message": "Tidak ada proses latar belakang yang aktif."},
            }
        )

    active_pids = list(BACKGROUND_PROCESSES.keys())
    return json.dumps({"success": True, "data": {"active_pids": active_pids}})


advanced_tool_definitions = glm.Tool(
    function_declarations=[
        glm.FunctionDeclaration(
            name="write_to_scratchpad",
            description="Menyimpan informasi (string) ke memori jangka pendek dengan sebuah kunci.",
            parameters=glm.Schema(
                type=Type.OBJECT,
                properties={
                    "key": glm.Schema(type=Type.STRING),
                    "value": glm.Schema(type=Type.STRING),
                },
                required=["key", "value"],
            ),
        ),
        glm.FunctionDeclaration(
            name="read_from_scratchpad",
            description="Membaca informasi dari memori jangka pendek menggunakan kunci.",
            parameters=glm.Schema(
                type=Type.OBJECT,
                properties={"key": glm.Schema(type=Type.STRING)},
                required=["key"],
            ),
        ),
        glm.FunctionDeclaration(
            name="start_background_process",
            description="Memulai perintah di latar belakang (misalnya server atau skrip interaktif) dan mengembalikan PID.",
            parameters=glm.Schema(
                type=Type.OBJECT,
                properties={
                    "command": glm.Schema(type=Type.STRING),
                    "args": glm.Schema(
                        type=Type.ARRAY, items=glm.Schema(type=Type.STRING)
                    ),
                },
                required=["command"],
            ),
        ),
        glm.FunctionDeclaration(
            name="send_input_to_process",
            description="Mengirim string input ke proses latar belakang yang sedang berjalan (misalnya, memilih menu).",
            parameters=glm.Schema(
                type=Type.OBJECT,
                properties={
                    "pid": glm.Schema(type=Type.NUMBER),
                    "input_string": glm.Schema(type=Type.STRING),
                },
                required=["pid", "input_string"],
            ),
        ),
        glm.FunctionDeclaration(
            name="check_process_status",
            description="Memeriksa status (berjalan/selesai) dan output dari proses latar belakang yang sudah selesai.",
            parameters=glm.Schema(
                type=Type.OBJECT,
                properties={"pid": glm.Schema(type=Type.NUMBER)},
                required=["pid"],
            ),
        ),
        glm.FunctionDeclaration(
            name="stop_process",
            description="Menghentikan proses latar belakang berdasarkan PID-nya.",
            parameters=glm.Schema(
                type=Type.OBJECT,
                properties={"pid": glm.Schema(type=Type.NUMBER)},
                required=["pid"],
            ),
        ),
        glm.FunctionDeclaration(
            name="list_running_processes",
            description="Melihat daftar PID dari semua proses latar belakang yang saat ini aktif.",
            parameters=glm.Schema(type=Type.OBJECT, properties={}),
        ),
    ]
)

advanced_functions = {
    "write_to_scratchpad": write_to_scratchpad,
    "read_from_scratchpad": read_from_scratchpad,
    "start_background_process": start_background_process,
    "send_input_to_process": send_input_to_process,
    "check_process_status": check_process_status,
    "stop_process": stop_process,
    "list_running_processes": list_running_processes,
}
