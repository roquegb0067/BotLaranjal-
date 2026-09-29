import os
import requests
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()

# Correção: Adicionadas aspas para buscar a variável de ambiente
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Correção: Adicionadas aspas para definir a string de texto
texto = "O que acha de ser um robo Otto de assistente de IA para um projeto do colégio?"

def perguntar_gemini(texto):
    if not GEMINI_API_KEY:
        return "Erro: chave da API não configurada."
    
    # Correção: URL formatada como string única e com o modelo correto
    url = "https://googleapis.com"
    
    # Correção: Adicionadas aspas em todas as chaves e valores do dicionário
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": GEMINI_API_KEY.strip()
    }
    
    # Correção: Alterado 'mensagem' para 'texto' para bater com o parâmetro da função
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
        
        # Correção: Adicionadas aspas para acessar as chaves do JSON retornado
        resultado = dados["candidates"][0]["content"]["parts"][0]["text"]
        return resultado
    except Exception as e:
        return f"Erro na API: {e}"

# Correção: Chamando a função corretamente e passando a variável 'texto'
print(perguntar_gemini(texto))
