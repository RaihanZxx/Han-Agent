import os
DIREKTORI_BATASAN_AI = os.path.abspath(os.path.join(os.getcwd(), "han_workspace"))

PROMPT_DIRECTORY = os.path.abspath(os.path.join(os.path.dirname(__file__), "prompt"))

GEMINI_MODEL_NAME = "gemini-2.5-flash-preview-05-20"
TOOL_CALL_PAUSE_SECONDS = 8