import google.ai.generativelanguage as glm
from google.ai.generativelanguage import Type
import json
from logging_handler import log_user_input
from utils.colors import Colors

USER_INPUT_REQUIRED = False
USER_RESPONSE = None

def signal_task_complete(final_summary):
    return json.dumps({
        "success": True,
        "data": f"Sinyal tugas selesai diterima. Ringkasan akhir: {final_summary}"
    })

def ask_user_for_input(question: str):
    global USER_INPUT_REQUIRED
    USER_INPUT_REQUIRED = True
    
    return json.dumps({
        "success": True,
        "data": {
            "type": "user_input_request",
            "question": question
        }
    })


control_tool_definitions = glm.Tool(
    function_declarations=[
        glm.FunctionDeclaration(
            name="signal_task_complete",
            description="Panggil ini HANYA SEKALI di akhir ketika SEMUA tugas telah berhasil diselesaikan.",
            parameters=glm.Schema(
                type=Type.OBJECT,
                properties={"final_summary": glm.Schema(type=Type.STRING, description="Ringkasan singkat tentang apa yang telah dicapai.")},
                required=["final_summary"]
            )
        ),
        glm.FunctionDeclaration(
            name="ask_user_for_input",
            description="Mengajukan pertanyaan kepada pengguna dan menjeda eksekusi. Gunakan untuk klarifikasi, keputusan, atau meminta data sensitif.",
            parameters=glm.Schema(
                type=Type.OBJECT,
                properties={"question": glm.Schema(type=Type.STRING, description="Pertanyaan yang akan diajukan kepada pengguna.")},
                required=["question"]
            )
        )
    ]
)

control_functions = {
    "signal_task_complete": signal_task_complete,
    "ask_user_for_input": ask_user_for_input,
}