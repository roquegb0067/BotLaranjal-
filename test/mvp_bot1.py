import os
import requests
from dotenv import load_dotenv
load_dotenv('kei.env')
def analisar_com_gemini(prompt_texto):
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_key:
        return {'sucesso': False, 'erro': 'GEMINI_API_KEY não configurada no kei.env'}

    parts = [{"text": prompt_texto}]


    # A chave PRECISA estar no parâmetro ?key= da URL para o endpoint v1beta
    API_KEY = gemini_key.strip()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={API_KEY}"

    headers = {
        "Content-Type": "application/json"
    }
    
    payload = {"contents": [{"parts": parts}]}

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        dados = response.json()

        if response.status_code != 200:
            return {'sucesso': False, 'erro': dados}

        candidates = dados.get('candidates', [])
        if not candidates:
            return {'sucesso': False, 'erro': 'Nenhuma resposta gerada.', 'detalhes': dados}

        parts_resposta = candidates[0].get('content', {}).get('parts', [])
        if not parts_resposta:
            finish_reason = candidates[0].get('finishReason', 'Desconhecido')
            return {
                'sucesso': False, 
                'erro': f'A resposta foi bloqueada ou interrompida (Motivo: {finish_reason}).'
            }

        texto_resposta = parts_resposta[0].get('text', '')
        return {'sucesso': True, 'analise': texto_resposta}

    except Exception as e:
        return {'sucesso': False, 'erro': str(e)}
# Guardando o resultado em uma variável
resultado = analisar_com_gemini("O que acha de ser um assistentede IA em um robo Otto para um projeto de escola?")

# Exibindo o resultado na tela
print(resultado)