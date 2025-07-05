import google.ai.generativelanguage as glm
from google.ai.generativelanguage import Type
import json
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS


def web_search(query: str, num_results: int = 5):
    try:
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=num_results)]

        if not results:
            return json.dumps(
                {"success": True, "data": "Tidak ada hasil pencarian yang ditemukan."}
            )

        formatted_results = []
        for r in results:
            formatted_results.append(
                f"Title: {r['title']}\nURL: {r['href']}\nSnippet: {r['body']}\n---"
            )

        return json.dumps({"success": True, "data": "\n".join(formatted_results)})
    except Exception as e:
        return json.dumps(
            {"success": False, "data": f"Gagal melakukan pencarian web: {e}"}
        )


def fetch_webpage_content(url: str):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")

        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()

        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = "\n".join(chunk for chunk in chunks if chunk)

        return json.dumps({"success": True, "data": text})
    except requests.RequestException as e:
        return json.dumps(
            {"success": False, "data": f"Gagal mengambil konten dari URL '{url}': {e}"}
        )
    except Exception as e:
        return json.dumps(
            {
                "success": False,
                "data": f"Terjadi kesalahan saat memproses URL '{url}': {e}",
            }
        )


internet_tool_definitions = glm.Tool(
    function_declarations=[
        glm.FunctionDeclaration(
            name="web_search",
            description="Melakukan pencarian web dan mengembalikan daftar hasil.",
            parameters=glm.Schema(
                type=Type.OBJECT,
                properties={
                    "query": glm.Schema(
                        type=Type.STRING, description="Query pencarian."
                    ),
                    "num_results": glm.Schema(
                        type=Type.NUMBER,
                        description="Jumlah hasil yang diinginkan (default: 5).",
                    ),
                },
                required=["query"],
            ),
        ),
        glm.FunctionDeclaration(
            name="fetch_webpage_content",
            description="Mengambil konten teks dari sebuah URL. Berguna untuk 'membaca' hasil pencarian.",
            parameters=glm.Schema(
                type=Type.OBJECT,
                properties={
                    "url": glm.Schema(
                        type=Type.STRING,
                        description="URL lengkap halaman web yang akan dibaca.",
                    )
                },
                required=["url"],
            ),
        ),
    ]
)

internet_functions = {
    "web_search": web_search,
    "fetch_webpage_content": fetch_webpage_content,
}
