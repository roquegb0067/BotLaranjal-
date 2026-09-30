import asyncio
import websockets
import json
import base64
import pyaudio
import os
API_KEY = os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("A variável GEMINI_API_KEY não foi configurada!")

MODEL_NAME = "gemini-3.8-live"
WS_URL = f"wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContent?key={API_KEY}"

# Configurações de Áudio (Formatos padrão aceitos pelo Gemini)
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000          # 16kHz exigido pela API
CHUNK_SIZE = 1024     # Tamanho do bloco de captura

# Inicializa o PyAudio
p = pyaudio.PyAudio()

# 1. FUNÇÃO PARA GRAVAR O MICROFONE E ENVIAR
async def send_mic_audio(websocket):
    # Abre o fluxo de entrada (Microfone)
    mic_stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK_SIZE
    )
    print("🎤 Microfone ligado! Pode falar...")

    try:
        while True:
            # Lê os bytes brutos (PCM) do microfone de forma não-bloqueante
            data = mic_stream.read(CHUNK_SIZE, exception_on_overflow=False)
            
            # Codifica em Base64
            encoded_data = base64.b64encode(data).decode('utf-8')
            
            # Monta a estrutura JSON da API
            audio_message = {
                "realtimeInput": {
                    "mediaChunks": [
                        {
                            "data": encoded_data,
                            "mimeType": "audio/pcm;rate=16000"
                        }
                    ]
                }
            }
            # Envia pelo WebSocket
            await websocket.send(json.dumps(audio_message))
            await asyncio.sleep(0.001) # Cede tempo para o loop assíncrono
            
    except asyncio.CancelledError:
        mic_stream.stop_stream()
        mic_stream.close()

# 2. FUNÇÃO PARA RECEBER E REPRODUZIR O ÁUDIO DO GEMINI
async def receive_and_play_audio(websocket):
    # Abre o fluxo de saída (Alto-falantes / Fone)
    speaker_stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=24000, # O Gemini costuma retornar áudio sintetizado em 24kHz
        output=True
    )
    print("🔊 Alto-falante pronto...")

    try:
        async for message in websocket:
            response = json.loads(message)

            # Verifica se na resposta há partes contendo dados de áudio
            server_content = response.get("serverContent", {})
            model_turn = server_content.get("modelTurn", {})
            parts = model_turn.get("parts", [])

             for part in parts:
                inline_data = part.get("inlineData", {})
                if inline_data.get("mimeType", "").startswith("audio/pcm"):
                    # 1. Decodifica o Base64
                    audio_bytes = base64.b64decode(inline_data["data"])
                    
                    # 2. Salva os bytes num arquivo temporario
                    with open("temp_response.pcm", "wb") as f:
                        f.write(audio_bytes)
                    
                    # 3. Manda o Android tocar o arquivo (vai direto pro fone Bluetooth)
                    import os
                    os.system("termux-media-player play temp_response.pcm")

    except asyncio.CancelledError:
        pass # Nao precisa fechar o speaker_stream se nao tiver usando o PyAudio no out


# 3. LOOP PRINCIPAL
async def main():
    async with websockets.connect(WS_URL) as websocket:
        print("WebSocket Conectado com Sucesso!")

        # Configuração inicial do modelo
        setup_message = {
            "setup": {
                "model": f"models/{MODEL_NAME}",
                "generationConfig": {
                    "responseModalities": ["AUDIO"] # Exige resposta em Voz
                }
            }
        }
        await websocket.send(json.dumps(setup_message))

        # Executa a gravação e a reprodução simultaneamente em tarefas assíncronas
        send_task = asyncio.create_task(send_mic_audio(websocket))
        receive_task = asyncio.create_task(receive_and_play_audio(websocket))

        # Mantém as duas tarefas rodando em paralelo
        await asyncio.gather(send_task, receive_task)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nEncerrado pelo usuário.")
        p.terminate()
