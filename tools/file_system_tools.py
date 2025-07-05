import os
import shutil
import google.ai.generativelanguage as glm
from google.ai.generativelanguage import Type
import zipfile
import json

from utils.path_utils import sanitize_path


def _json_response(success, data):
    return json.dumps({"success": success, "data": data})


def create_directory(path):
    try:
        full_path = sanitize_path(path)
        os.makedirs(full_path, exist_ok=True)
        return _json_response(True, f"Direktori '{path}' berhasil dibuat.")
    except ValueError as e:
        return _json_response(False, f"Kesalahan keamanan: {e}")
    except Exception as e:
        return _json_response(False, f"Gagal membuat direktori '{path}': {e}")


def read_file(filename):
    try:
        full_path = sanitize_path(filename)
        if not os.path.isfile(full_path):
            return _json_response(
                False, f"File '{filename}' tidak ditemukan atau bukan file."
            )
        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        return _json_response(True, content)
    except ValueError as e:
        return _json_response(False, f"Kesalahan keamanan: {e}")
    except Exception as e:
        return _json_response(False, f"Gagal membaca file '{filename}': {e}")


def write_file(filename, content):
    try:
        full_path = sanitize_path(filename)
        parent_dir = os.path.dirname(full_path)
        os.makedirs(parent_dir, exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        return _json_response(True, f"File '{filename}' berhasil ditulis.")
    except ValueError as e:
        return _json_response(False, f"Kesalahan keamanan: {e}")
    except Exception as e:
        return _json_response(False, f"Gagal menulis ke file '{filename}': {e}")


def list_directory(path="."):
    try:
        full_path = sanitize_path(path)
        if not os.path.isdir(full_path):
            return _json_response(
                False, f"Error: '{path}' bukan direktori atau tidak ditemukan."
            )
        items = os.listdir(full_path)
        return _json_response(True, items)
    except ValueError as e:
        return _json_response(False, f"Kesalahan keamanan: {e}")
    except Exception as e:
        return _json_response(False, f"Gagal melihat isi direktori '{path}': {e}")


def delete_file(filename):
    try:
        full_path = sanitize_path(filename)
        if os.path.isfile(full_path):
            os.remove(full_path)
            return _json_response(True, f"File '{filename}' berhasil dihapus.")
        else:
            return _json_response(
                False, f"File '{filename}' tidak ditemukan atau bukan file."
            )
    except ValueError as e:
        return _json_response(False, f"Kesalahan keamanan: {e}")
    except Exception as e:
        return _json_response(False, f"Gagal menghapus file '{filename}': {e}")


def create_zip_archive(source_paths, output_zip_path):
    try:
        full_output_zip_path = sanitize_path(output_zip_path)
        output_dir = os.path.dirname(full_output_zip_path)
        os.makedirs(output_dir, exist_ok=True)

        with zipfile.ZipFile(full_output_zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for path in source_paths:
                full_source_path = sanitize_path(path)
                if not os.path.exists(full_source_path):
                    return _json_response(
                        False, f"Jalur sumber '{path}' tidak ditemukan."
                    )

                if os.path.isdir(full_source_path):
                    base_dir = os.path.dirname(full_source_path)
                    for root, dirs, files in os.walk(full_source_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, base_dir)
                            zipf.write(file_path, arcname)
                else:
                    arcname = os.path.basename(full_source_path)
                    zipf.write(full_source_path, arcname)

        return _json_response(True, f"Arsip ZIP '{output_zip_path}' berhasil dibuat.")
    except ValueError as e:
        return _json_response(False, f"Kesalahan keamanan: {e}")
    except Exception as e:
        return _json_response(
            False, f"Gagal membuat arsip ZIP '{output_zip_path}': {e}"
        )


def append_to_file(filename, content):
    try:
        full_path = sanitize_path(filename)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "a", encoding="utf-8") as f:
            f.write(content)
        return _json_response(
            True, f"Konten berhasil ditambahkan ke file '{filename}'."
        )
    except ValueError as e:
        return _json_response(False, f"Kesalahan keamanan: {e}")
    except Exception as e:
        return _json_response(False, f"Gagal menambahkan ke file '{filename}': {e}")


def move_item(source_path, destination_path):
    try:
        full_source_path = sanitize_path(source_path)
        full_destination_path = sanitize_path(destination_path)
        if not os.path.exists(full_source_path):
            return _json_response(False, f"Sumber '{source_path}' tidak ditemukan.")
        os.makedirs(os.path.dirname(full_destination_path), exist_ok=True)
        shutil.move(full_source_path, full_destination_path)
        return _json_response(
            True, f"'{source_path}' berhasil dipindahkan ke '{destination_path}'."
        )
    except ValueError as e:
        return _json_response(False, f"Kesalahan keamanan: {e}")
    except Exception as e:
        return _json_response(False, f"Gagal memindahkan '{source_path}': {e}")


file_system_tool_definitions = glm.Tool(
    function_declarations=[
        glm.FunctionDeclaration(
            name="create_directory",
            description="Membuat direktori baru. Mengembalikan JSON dengan status keberhasilan.",
            parameters=glm.Schema(
                type=Type.OBJECT,
                properties={"path": glm.Schema(type=Type.STRING)},
                required=["path"],
            ),
        ),
        glm.FunctionDeclaration(
            name="read_file",
            description="Membaca konten file. Mengembalikan JSON dengan 'success':true dan 'data':<konten_file> jika berhasil.",
            parameters=glm.Schema(
                type=Type.OBJECT,
                properties={"filename": glm.Schema(type=Type.STRING)},
                required=["filename"],
            ),
        ),
        glm.FunctionDeclaration(
            name="write_file",
            description="Menulis konten ke file (menimpa). Mengembalikan JSON dengan status keberhasilan.",
            parameters=glm.Schema(
                type=Type.OBJECT,
                properties={
                    "filename": glm.Schema(type=Type.STRING),
                    "content": glm.Schema(type=Type.STRING),
                },
                required=["filename", "content"],
            ),
        ),
        glm.FunctionDeclaration(
            name="append_to_file",
            description="Menambahkan konten ke akhir file. Mengembalikan JSON dengan status keberhasilan.",
            parameters=glm.Schema(
                type=Type.OBJECT,
                properties={
                    "filename": glm.Schema(type=Type.STRING),
                    "content": glm.Schema(type=Type.STRING),
                },
                required=["filename", "content"],
            ),
        ),
        glm.FunctionDeclaration(
            name="list_directory",
            description="Melihat daftar isi direktori. Mengembalikan JSON dengan 'success':true dan 'data':[<daftar_item>] jika berhasil.",
            parameters=glm.Schema(
                type=Type.OBJECT, properties={"path": glm.Schema(type=Type.STRING)}
            ),
        ),
        glm.FunctionDeclaration(
            name="delete_file",
            description="Menghapus file. Mengembalikan JSON dengan status keberhasilan.",
            parameters=glm.Schema(
                type=Type.OBJECT,
                properties={"filename": glm.Schema(type=Type.STRING)},
                required=["filename"],
            ),
        ),
        glm.FunctionDeclaration(
            name="move_item",
            description="Memindahkan/mengganti nama file atau direktori. Mengembalikan JSON dengan status keberhasilan.",
            parameters=glm.Schema(
                type=Type.OBJECT,
                properties={
                    "source_path": glm.Schema(type=Type.STRING),
                    "destination_path": glm.Schema(type=Type.STRING),
                },
                required=["source_path", "destination_path"],
            ),
        ),
        glm.FunctionDeclaration(
            name="create_zip_archive",
            description="Membuat arsip ZIP dari file atau direktori. Mengembalikan JSON dengan status keberhasilan.",
            parameters=glm.Schema(
                type=Type.OBJECT,
                properties={
                    "source_paths": glm.Schema(
                        type=Type.ARRAY, items=glm.Schema(type=Type.STRING)
                    ),
                    "output_zip_path": glm.Schema(type=Type.STRING),
                },
                required=["source_paths", "output_zip_path"],
            ),
        ),
    ]
)

file_system_functions = {
    "create_directory": create_directory,
    "read_file": read_file,
    "write_file": write_file,
    "append_to_file": append_to_file,
    "list_directory": list_directory,
    "delete_file": delete_file,
    "move_item": move_item,
    "create_zip_archive": create_zip_archive,
}
