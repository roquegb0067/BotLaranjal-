import os
import requests
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()

texto = "O que acha de ser um robo Otto de assistente de IA para um projeto do colégio?"

def perguntar_gemini(texto):
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_key:
        return {'sucesso': False, 'erro': 'GEMINI_API_KEY não configurada no arquivo .env'}
    
    api_key = gemini_key.strip()
    
    # Modelo oficial do Gemini (use gemini-1.5-flash ou gemini-2.0-flash)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": texto
                    }
                ]
            }
        ]
    }
    
    try:
        resposta = requests.post(url, headers=headers, json=payload, timeout=30)
        resposta.raise_for_status()
        dados = resposta.json()
        
        # Extrai a resposta da API
        resultado = dados["candidates"][0]["content"]["parts"][0]["text"]
        return resultado
    except Exception as e:
        return f"Erro na API: {e}"

# Executa e exibe o resultado
print(perguntar_gemini(texto))
