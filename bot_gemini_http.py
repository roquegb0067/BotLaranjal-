import os
import base64
import requests
from flask import Flask, request, jsonify, send_file
from dotenv import load_dotenv
from gtts import gTTS

# Carrega as variáveis do arquivo .env / kei.env
load_dotenv('kei.env')

app = Flask(__name__)

def processar_com_gemini(prompt_texto=None, arquivo_audio=None):
    """
    Envia o texto ou áudio de entrada diretamente para a API do Gemini.
    """
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_key:
        return {'sucesso': False, 'erro': 'GEMINI_API_KEY não configurada no arquivo de ambiente.'}

    parts = []

    # Se recebeu texto, adiciona às partes
    if prompt_texto:
        parts.append({"text": prompt_texto})

    # Se recebeu áudio, converte para base64 e envia como inline_data
    if arquivo_audio and arquivo_audio.filename != '':
        bytes_audio = arquivo_audio.read()
        audio_b64 = base64.b64encode(bytes_audio).decode('utf-8')
        
        # Identifica o tipo MIME do áudio (ex: audio/mp3, audio/wav, audio/ogg)
        mime_type = arquivo_audio.mimetype or 'audio/mp3'

        parts.append({
            "inline_data": {
                "mime_type": mime_type,
                "data": audio_b64
            }
        })
        
        # Adiciona instrução no prompt se nenhum texto explicitado foi enviado
        if not prompt_texto:
            parts.append({"text": "Ouça o áudio acima e responda de forma clara e objetiva em português."})

    if not parts:
        return {'sucesso': False, 'erro': 'Nenhum texto ou arquivo de áudio foi fornecido.'}

    API_KEY = gemini_key.strip()
    
    # Modelo oficial compatível com texto e áudio multimodais
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={API_KEY}"
    headers = {
        "Content-Type": "application/json"
    }
    
    payload = {"contents": [{"parts": parts}]}

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=45)
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
        return {'sucesso': True, 'resposta': texto_resposta}

    except Exception as e:
        return {'sucesso': False, 'erro': str(e)}


@app.route('/ia/conversar', methods=['POST'])
def escutar_e_responder():
    """
    Endpoint que escuta requisições contendo texto ou arquivo de áudio.
    Retorna a resposta em JSON + caminho/link para o áudio gerado.
    """
    prompt_texto = request.form.get('texto')
    arquivo_audio = request.files.get('audio')

    if not prompt_texto and not arquivo_audio:
        return jsonify({
            'sucesso': False, 
            'erro': 'Envie pelo menos um campo: "texto" (Form-Data) ou "audio" (File).'
        }), 400

    # 1. Processa no Gemini
    resultado_gemini = processar_com_gemini(prompt_texto, arquivo_audio)

    if not resultado_gemini.get('sucesso'):
        return jsonify(resultado_gemini), 400

    texto_resposta = resultado_gemini.get('resposta')

    # 2. Converte a resposta em áudio usando gTTS (Google Text-to-Speech)
    caminho_audio_resposta = "resposta_gemini.mp3"
    try:
        tts = gTTS(text=texto_resposta, lang='pt', tld='com.br')
        tts.save(caminho_audio_resposta)
        gerou_audio = True
    except Exception as e:
        gerou_audio = False

    return jsonify({
        'sucesso': True,
        'resposta_texto': texto_resposta,
        'audio_disponivel': gerou_audio,
        'url_audio': '/ia/download-audio' if gerou_audio else None
    })


@app.route('/ia/download-audio', methods=['GET'])
def baixar_audio_resposta():
    """Endpoint para baixar/tocar o áudio gerado pela resposta."""
    caminho_audio = "resposta_gemini.mp3"
    if os.path.exists(caminho_audio):
        return send_file(caminho_audio, mimetype="audio/mp3")
    return jsonify({'erro': 'Arquivo de áudio não encontrado.'}), 404


if __name__ == '__main__':
    # Roda o servidor escutando em todas as interfaces na porta 5000
    app.run(host='0.0.0.0', port=5000, debug=True)
