import os
import shutil
import google.ai.generativelanguage as glm
from google.ai.generativelanguage import Type
import zipfile

from utils.path_utils import sanitize_path
from config import DIREKTORI_BATASAN_AI

def create_directory(path):
    try:
        full_path = sanitize_path(path)
        os.makedirs(full_path, exist_ok=True)
        return f"Direktori '{path}' berhasil dibuat."
    except ValueError as e:
        return f"Kesalahan keamanan: {e}"
    except Exception as e:
        return f"Gagal membuat direktori '{path}': {e}"

def read_file(filename):
    try:
        full_path = sanitize_path(filename)
        if not os.path.isfile(full_path):
            return f"File '{filename}' tidak ditemukan atau bukan file."
        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        return f"Konten dari '{filename}':\n{content}"
    except ValueError as e:
        return f"Kesalahan keamanan: {e}"
    except FileNotFoundError:
        return f"File '{filename}' tidak ditemukan."
    except PermissionError:
        return f"Izin ditolak untuk membaca file '{filename}'."
    except Exception as e:
        return f"Gagal membaca file '{filename}': {e}"

def write_file(filename, content):
    try:
        full_path = sanitize_path(filename)
        parent_dir = os.path.dirname(full_path)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"File '{filename}' berhasil ditulis."
    except ValueError as e:
        return f"Kesalahan keamanan: {e}"
    except PermissionError:
        return f"Izin ditolak untuk menulis ke file '{filename}'."
    except Exception as e:
        return f"Gagal menulis ke file '{filename}': {e}"

def append_to_file(filename, content):
    try:
        full_path = sanitize_path(filename)
        parent_dir = os.path.dirname(full_path)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)
        with open(full_path, 'a', encoding='utf-8') as f:
            f.write(content)
        return f"Konten berhasil ditambahkan ke file '{filename}'."
    except ValueError as e:
        return f"Kesalahan keamanan: {e}"
    except FileNotFoundError:
        return f"File '{filename}' tidak ditemukan saat mencoba menambahkan konten."
    except PermissionError:
        return f"Izin ditolak untuk menambahkan konten ke file '{filename}'."
    except Exception as e:
        return f"Gagal menambahkan konten ke file '{filename}': {e}"

def list_directory(path='.'):
    try:
        full_path = sanitize_path(path)
        if not os.path.isdir(full_path):
            return f"Error: '{path}' bukan direktori atau tidak ditemukan."

        items = os.listdir(full_path)
        visible_items = [item for item in items if not item.startswith('.')]

        if not visible_items:
            return f"Direktori '{path}' kosong atau hanya berisi file tersembunyi."

        return f"Isi direktori '{path}':\n" + "\n".join(visible_items)
    except ValueError as e:
        return f"Kesalahan keamanan: {e}"
    except FileNotFoundError:
        return f"Direktori '{path}' tidak ditemukan."
    except PermissionError:
        return f"Izin ditolak untuk melihat isi direktori '{path}'."
    except Exception as e:
        return f"Gagal melihat isi direktori '{path}': {e}"

def delete_file(filename):
    try:
        full_path = sanitize_path(filename)
        if os.path.exists(full_path) and os.path.isfile(full_path):
            os.remove(full_path)
            return f"File '{filename}' berhasil dihapus."
        else:
            return f"File '{filename}' tidak ditemukan atau bukan file."
    except ValueError as e:
        return f"Kesalahan keamanan: {e}"
    except PermissionError:
        return f"Izin ditolak untuk menghapus file '{filename}'."
    except Exception as e:
        return f"Gagal menghapus file '{filename}': {e}"

def copy_file(source_path, destination_path):
    try:
        full_source_path = sanitize_path(source_path)
        full_destination_path = sanitize_path(destination_path)

        if not os.path.isfile(full_source_path):
            return f"File sumber '{source_path}' tidak ditemukan."

        parent_dir = os.path.dirname(full_destination_path)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)

        shutil.copy2(full_source_path, full_destination_path)
        return f"File '{source_path}' berhasil disalin ke '{destination_path}'."
    except ValueError as e:
        return f"Kesalahan keamanan: {e}"
    except FileNotFoundError:
        return f"File sumber '{source_path}' tidak ditemukan."
    except PermissionError:
        return f"Izin ditolak untuk menyalin file atau menulis ke '{destination_path}'."
    except Exception as e:
        return f"Gagal menyalin file '{source_path}' ke '{destination_path}': {e}"

def move_item(source_path, destination_path):
    try:
        full_source_path = sanitize_path(source_path)
        full_destination_path = sanitize_path(destination_path)

        if not os.path.exists(full_source_path):
            return f"Sumber '{source_path}' tidak ditemukan."

        parent_dir = os.path.dirname(full_destination_path)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)

        shutil.move(full_source_path, full_destination_path)
        return f"'{source_path}' berhasil dipindahkan ke '{destination_path}'."
    except ValueError as e:
        return f"Kesalahan keamanan: {e}"
    except FileNotFoundError:
        return f"Sumber '{source_path}' tidak ditemukan."
    except PermissionError:
        return f"Izin ditolak untuk memindahkan item atau menulis ke '{destination_path}'."
    except Exception as e:
        return f"Gagal memindahkan '{source_path}' ke '{destination_path}': {e}"

def rename_item(old_path, new_path):
    try:
        full_old_path = sanitize_path(old_path)
        full_new_path = sanitize_path(new_path)

        if not os.path.exists(full_old_path):
            return f"Item '{old_path}' tidak ditemukan."

        if os.path.dirname(full_old_path) != os.path.dirname(full_new_path):
            return f"Error: Fungsi rename_item hanya bisa mengganti nama dalam direktori yang sama. Gunakan move_item untuk memindahkan."

        os.rename(full_old_path, full_new_path)
        return f"'{old_path}' berhasil diganti nama menjadi '{new_path}'."
    except ValueError as e:
        return f"Kesalahan keamanan: {e}"
    except FileNotFoundError:
        return f"Item '{old_path}' tidak ditemukan."
    except PermissionError:
        return f"Izin ditolak untuk mengganti nama '{old_path}'."
    except Exception as e:
        return f"Gagal mengganti nama '{old_path}' menjadi '{new_path}': {e}"

def delete_directory(path):
    try:
        full_path = sanitize_path(path)

        if full_path == DIREKTORI_BATASAN_AI:
            return "Kesalahan keamanan: Tidak diizinkan menghapus direktori kerja AI utama."

        if os.path.exists(full_path) and os.path.isdir(full_path):
            shutil.rmtree(full_path)
            return f"Direktori '{path}' berhasil dihapus beserta isinya."
        else:
            return f"Direktori '{path}' tidak ditemukan atau bukan direktori."
    except ValueError as e:
        return f"Kesalahan keamanan: {e}"
    except PermissionError:
        return f"Izin ditolak untuk menghapus direktori '{path}'."
    except Exception as e:
        return f"Gagal menghapus direktori '{path}': {e}"

def check_path_exists(path):
    try:
        full_path = sanitize_path(path)
        if os.path.exists(full_path):
            return f"Jalur '{path}' ditemukan."
        else:
            return f"Jalur '{path}' tidak ditemukan."
    except ValueError as e:
        return f"Kesalahan keamanan: {e}"
    except Exception as e:
        return f"Gagal memeriksa keberadaan jalur '{path}': {e}"

def get_item_type(path):
    try:
        full_path = sanitize_path(path)
        if not os.path.exists(full_path):
            return f"Jalur '{path}' tidak ditemukan."
        elif os.path.isfile(full_path):
            return f"Jalur '{path}' adalah file."
        elif os.path.isdir(full_path):
            return f"Jalur '{path}' adalah direktori."
        else:
            return f"Jalur '{path}' ada, tetapi bukan file atau direktori (misalnya, symlink, device file)."
    except ValueError as e:
        return f"Kesalahan keamanan: {e}"
    except Exception as e:
        return f"Gagal mendeteksi tipe jalur '{path}': {e}"

def get_file_size(filename):
    try:
        full_path = sanitize_path(filename)
        if not os.path.isfile(full_path):
            return f"File '{filename}' tidak ditemukan atau bukan file."
        size_bytes = os.path.getsize(full_path)
        return f"Ukuran file '{filename}': {size_bytes} bytes."
    except ValueError as e:
        return f"Kesalahan keamanan: {e}"
    except FileNotFoundError:
        return f"File '{filename}' tidak ditemukan."
    except PermissionError:
        return f"Izin ditolak untuk mendapatkan ukuran file '{filename}'."
    except Exception as e:
        return f"Gagal mendapatkan ukuran file '{filename}': {e}"

def search_file_content(filename, query, case_sensitive=False):
    try:
        full_path = sanitize_path(filename)
        if not os.path.isfile(full_path):
            return f"File '{filename}' tidak ditemukan atau bukan file."

        matches = []
        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                if case_sensitive:
                    if query in line:
                        matches.append(f"Line {line_num}: {line.strip()}")
                else:
                    if query.lower() in line.lower():
                        matches.append(f"Line {line_num}: {line.strip()}")

        if matches:
            return f"Ditemukan '{query}' di '{filename}':\n" + "\n".join(matches)
        else:
            return f"Tidak ditemukan '{query}' di '{filename}'."
    except ValueError as e:
        return f"Kesalahan keamanan: {e}"
    except FileNotFoundError:
        return f"File '{filename}' tidak ditemukan."
    except PermissionError:
        return f"Izin ditolak untuk membaca file '{filename}'."
    except Exception as e:
        return f"Gagal mencari di file '{filename}': {e}"

def create_zip_archive(source_paths, output_zip_path):
    try:
        full_output_zip_path = sanitize_path(output_zip_path)
        
        output_dir = os.path.dirname(full_output_zip_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        with zipfile.ZipFile(full_output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for path in source_paths:
                full_source_path = sanitize_path(path)
                if not os.path.exists(full_source_path):
                    return f"Peringatan: Jalur sumber '{path}' tidak ditemukan. Akan mencoba melanjutkan dengan yang lain.\n"

                if os.path.isfile(full_source_path):
                    zipf.write(full_source_path, os.path.relpath(full_source_path, DIREKTORI_BATASAN_AI))
                elif os.path.isdir(full_source_path):
                    for root, dirs, files in os.walk(full_source_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, DIREKTORI_BATASAN_AI)
                            zipf.write(file_path, arcname)
                        for dir_name in dirs:
                            dir_path = os.path.join(root, dir_name)
                            arcname = os.path.relpath(dir_path, DIREKTORI_BATASAN_AI)
                            if not os.listdir(dir_path):
                                zif = zipfile.ZipInfo(arcname + '/')
                                zipf.writestr(zif, '')
                else:
                    return f"Peringatan: Jalur '{path}' bukan file atau direktori yang valid. Dilewati.\n"
        
        return f"Arsip ZIP '{output_zip_path}' berhasil dibuat dari {len(source_paths)} item."
    except ValueError as e:
        return f"Kesalahan keamanan: {e}"
    except Exception as e:
        return f"Gagal membuat arsip ZIP '{output_zip_path}': {e}"


file_system_tool_definitions = glm.Tool(
    function_declarations=[
        glm.FunctionDeclaration(name="create_directory", description="Membuat direktori baru pada sistem file. Gunakan ini untuk mengatur struktur direktori.", parameters=glm.Schema(type=Type.OBJECT, properties={"path": glm.Schema(type=Type.STRING, description="Jalur lengkap direktori yang akan dibuat relatif terhadap workspace AI.")}, required=["path"])),
        glm.FunctionDeclaration(name="read_file", description="Membaca konten file yang ada.", parameters=glm.Schema(type=Type.OBJECT, properties={"filename": glm.Schema(type=Type.STRING, description="Nama atau jalur file yang akan dibaca relatif terhadap workspace AI.")}, required=["filename"])),
        glm.FunctionDeclaration(name="write_file", description="Menulis konten ke file (akan menimpa jika file sudah ada). Hati-hati menggunakannya agar tidak kehilangan data.", parameters=glm.Schema(type=Type.OBJECT, properties={"filename": glm.Schema(type=Type.STRING, description="Nama atau jalur file yang akan ditulis relatif terhadap workspace AI."), "content": glm.Schema(type=Type.STRING, description="Konten yang akan ditulis ke file.")}, required=["filename", "content"])),
        glm.FunctionDeclaration(name="append_to_file", description="Menambahkan konten ke akhir file.", parameters=glm.Schema(type=Type.OBJECT, properties={"filename": glm.Schema(type=Type.STRING, description="Nama atau jalur file yang akan ditambahkan konten relatif terhadap workspace AI."), "content": glm.Schema(type=Type.STRING, description="Konten yang akan ditambahkan ke file.")}, required=["filename", "content"])),
        glm.FunctionDeclaration(name="list_directory", description="Melihat daftar isi direktori yang diberikan.", parameters=glm.Schema(type=Type.OBJECT, properties={"path": glm.Schema(type=Type.STRING, description="Jalur direktori yang akan dilihat isinya relatif terhadap workspace AI. Defaultnya adalah direktori saat ini ('.').")}, required=[])),
        glm.FunctionDeclaration(name="delete_file", description="Menghapus file yang diberikan. Ini adalah tindakan permanen dan tidak dapat dibatalkan. Gunakan dengan sangat hati-hati!", parameters=glm.Schema(type=Type.OBJECT, properties={"filename": glm.Schema(type=Type.STRING, description="Nama atau jalur file yang akan dihapus relatif terhadap workspace AI.")}, required=["filename"])),
        glm.FunctionDeclaration(name="copy_file", description="Menyalin file dari satu lokasi ke lokasi lain. Akan membuat direktori tujuan jika belum ada.", parameters=glm.Schema(type=Type.OBJECT, properties={"source_path": glm.Schema(type=Type.STRING, description="Jalur file sumber relatif terhadap workspace AI."), "destination_path": glm.Schema(type=Type.STRING, description="Jalur tujuan untuk menyalin file relatif terhadap workspace AI.")}, required=["source_path", "destination_path"])),
        glm.FunctionDeclaration(name="move_item", description="Memindahkan file atau direktori dari sumber ke tujuan. Ini juga bisa digunakan untuk mengganti nama item jika tujuan berada di direktori yang sama. Akan membuat direktori tujuan jika belum ada.", parameters=glm.Schema(type=Type.OBJECT, properties={"source_path": glm.Schema(type=Type.STRING, description="Jalur file atau direktori sumber relatif terhadap workspace AI."), "destination_path": glm.Schema(type=Type.STRING, description="Jalur tujuan untuk memindahkan item relatif terhadap workspace AI.")}, required=["source_path", "destination_path"])),
        glm.FunctionDeclaration(name="rename_item", description="Mengganti nama file atau direktori yang ada di direktori yang sama.", parameters=glm.Schema(type=Type.OBJECT, properties={"old_path": glm.Schema(type=Type.STRING, description="Jalur lama file atau direktori relatif terhadap workspace AI."), "new_path": glm.Schema(type=Type.STRING, description="Jalur baru (nama baru) file atau direktori relatif terhadap workspace AI.")}, required=["old_path", "new_path"])),
        glm.FunctionDeclaration(name="delete_directory", description="Menghapus direktori beserta semua isinya (rekursif). Ini adalah tindakan yang *sangat berbahaya* dan tidak dapat dibatalkan. Gunakan dengan *sangat hati-hati* dan pastikan direktori kosong jika tidak ingin menghapus isinya.", parameters=glm.Schema(type=Type.OBJECT, properties={"path": glm.Schema(type=Type.STRING, description="Jalur direktori yang akan dihapus relatif terhadap workspace AI.")}, required=["path"])),
        glm.FunctionDeclaration(name="check_path_exists", description="Memeriksa apakah suatu file atau direktori ada di jalur yang diberikan.", parameters=glm.Schema(type=Type.OBJECT, properties={"path": glm.Schema(type=Type.STRING, description="Jalur file atau direktori yang akan diperiksa relatif terhadap workspace AI.")}, required=["path"])),
        glm.FunctionDeclaration(name="get_item_type", description="Mendeteksi apakah suatu jalur adalah file, direktori, atau tidak ada.", parameters=glm.Schema(type=Type.OBJECT, properties={"path": glm.Schema(type=Type.STRING, description="Jalur yang akan diperiksa relatif terhadap workspace AI.")}, required=["path"])),
        glm.FunctionDeclaration(name="get_file_size", description="Mendapatkan ukuran file dalam byte.", parameters=glm.Schema(type=Type.OBJECT, properties={"filename": glm.Schema(type=Type.STRING, description="Nama atau jalur file yang akan diambil ukurannya relatif terhadap workspace AI.")}, required=["filename"])),
        glm.FunctionDeclaration(name="search_file_content", description="Mencari string tertentu di dalam konten file dan mengembalikan baris yang cocok.", parameters=glm.Schema(type=Type.OBJECT, properties={"filename": glm.Schema(type=Type.STRING, description="Nama atau jalur file yang akan dicari relatif terhadap workspace AI."), "query": glm.Schema(type=Type.STRING, description="String yang ingin dicari."), "case_sensitive": glm.Schema(type=Type.BOOLEAN, description="True jika pencarian harus case-sensitive, False jika tidak (default: False).")}, required=["filename", "query"])),
        glm.FunctionDeclaration(
            name="create_zip_archive",
            description="Membuat arsip ZIP dari daftar file atau direktori yang diberikan. Berguna untuk mengemas proyek atau modul.",
            parameters=glm.Schema(
                type=Type.OBJECT,
                properties={
                    "source_paths": glm.Schema(type=Type.ARRAY, items=glm.Schema(type=Type.STRING), description="Daftar jalur file atau direktori yang akan di-zip, relatif terhadap workspace AI. Contoh: ['src/file1.py', 'docs/', 'images/logo.png']"),
                    "output_zip_path": glm.Schema(type=Type.STRING, description="Jalur dan nama file ZIP output (misal: 'my_project.zip' atau 'dist/module.zip'), relatif terhadap workspace AI.")
                },
                required=["source_paths", "output_zip_path"]
            )
        )
    ]
)

file_system_functions = {
    "create_directory": create_directory,
    "read_file": read_file,
    "write_file": write_file,
    "append_to_file": append_to_file,
    "list_directory": list_directory,
    "delete_file": delete_file,
    "copy_file": copy_file,
    "move_item": move_item,
    "rename_item": rename_item,
    "delete_directory": delete_directory,
    "check_path_exists": check_path_exists,
    "get_item_type": get_item_type,
    "get_file_size": get_file_size,
    "search_file_content": search_file_content,
    "create_zip_archive": create_zip_archive,
}