import os
import requests
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
texto = "O que acha de ser um robo Ottode assistente de IA para um projeto do colégio?"

resposta = perguntar_gemini(texto)
def perguntar_gemini(mensagem):

    if not GEMINI_API_KEY:
        return "Erro: chave da API não configurada."

    url = (
        "https://generativelanguage.googleapis.com/v1beta/"
        "models/gemini-3.5-flash-lite:generateContent"
    )

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": GEMINI_API_KEY.strip()
    }

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": mensagem
                    }
                ]
            }
        ]
    }

    try:
        resposta = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=30
        )

        resposta.raise_for_status()

        dados = resposta.json()

        texto = dados["candidates"][0]["content"]["parts"][0]["text"]

        return texto

    except Exception as e:
        return f"Erro na API: {e}"
print(resposta)