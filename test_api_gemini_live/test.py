import asyncio
import websockets
import json
import base64
import pyaudio
import os

API_KEY = os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("A variável GEMINI_API_KEY não foi configurada!")

# Modelo correto para a API Live (Bidi WebSocket)
MODEL_NAME = "gemini-3.8-live"
WS_URL = f"wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContent?key={API_KEY}"

# Configurações de Áudio
FORMAT = pyaudio.paInt16
CHANNELS = 1
INPUT_RATE = 16000      # Entrada exige 16kHz
OUTPUT_RATE = 24000     # Saída do Gemini é 24kHz
CHUNK_SIZE = 1024

# Inicializa o PyAudio
p = pyaudio.PyAudio()


# 1. FUNÇÃO PARA GRAVAR O MICROFONE E ENVIAR CONTINUAMENTE
async def send_mic_audio(websocket):
    mic_stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=INPUT_RATE,
        input=True,
        frames_per_buffer=CHUNK_SIZE
    )
    print("🎤 Microfone ativo! Pode falar...")

    try:
        while True:
            # Leitura do microfone fora do loop principal para não travar o asyncio
            data = await asyncio.to_thread(
                mic_stream.read,
                CHUNK_SIZE,
                exception_on_overflow=False
            )

            encoded_data = base64.b64encode(data).decode("utf-8")

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

            await websocket.send(json.dumps(audio_message))
            await asyncio.sleep(0.001)

    except asyncio.CancelledError:
        pass
    finally:
        mic_stream.stop_stream()
        mic_stream.close()


# 2. FUNÇÃO PARA RECEBER E REPRODUZIR O ÁUDIO DO GEMINI
async def receive_and_play_audio(websocket):
    speaker_stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=OUTPUT_RATE,
        output=True,
        frames_per_buffer=1024
    )

    print("🔊 Alto-falante pronto...")

    try:
        async for message in websocket:
            response = json.loads(message)

            if "error" in response:
                print(f"\n❌ Erro retornado pelo Gemini: {response['error']}")
                break

            server_content = response.get("serverContent", {})
            model_turn = server_content.get("modelTurn", {})
            parts = model_turn.get("parts", [])

            for part in parts:
                inline_data = part.get("inlineData", {})

                if inline_data.get("mimeType", "").startswith("audio/pcm"):
                    audio_bytes = base64.b64decode(inline_data["data"])
                    # Reprodução não-bloqueante para evitar gargalos na rede
                    await asyncio.to_thread(speaker_stream.write, audio_bytes)

            if server_content.get("turnComplete"):
                print("\n✅ Gemini concluiu a resposta.")

    except asyncio.CancelledError:
        pass
    finally:
        speaker_stream.stop_stream()
        speaker_stream.close()


# 3. MAIN (CONEXÃO E ORQUESTRAÇÃO)
async def main():
    async with websockets.connect(WS_URL) as websocket:
        print("🔗 WebSocket conectado com sucesso!")

        # Handshake inicial / Configuração do modelo
        setup_message = {
            "setup": {
                "model": f"models/{MODEL_NAME}",
                "generationConfig": {
                    "responseModalities": ["AUDIO"]
                }
            }
        }
        await websocket.send(json.dumps(setup_message))

        # Aguarda a confirmação de Handshake
        first_response = await websocket.recv()
        setup_ack = json.loads(first_response)

        if "setupComplete" in setup_ack:
            print("✅ Handshake concluído. Inicializando áudio...\n")
        else:
            print("⚠️ Resposta do setup:", setup_ack)

        # Inicia captura e reprodução simultaneamente
        send_task = asyncio.create_task(send_mic_audio(websocket))
        receive_task = asyncio.create_task(receive_and_play_audio(websocket))

        await asyncio.gather(send_task, receive_task)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Encerrado pelo usuário.")
    finally:
        p.terminate()
