import asyncio
import websockets
import json
import os

API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("A variável GEMINI_API_KEY não foi configurada!")

MODEL_NAME = "gemini-3.8-live"
GEMINI_WS_URL = f"wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContent?key={API_KEY}"

async def process_request(connection, request):
    # Se NÃO for uma requisição WebSocket, entrega o arquivo HTML
    if request.headers.get("Upgrade", "").lower() != "websocket":
        try:
            with open("index.html", "rb") as f:
                content = f.read()
            return (200, [("Content-Type", "text/html; charset=utf-8")], content)
        except FileNotFoundError:
            return (404, [("Content-Type", "text/plain")], b"Arquivo HTML nao encontrado.")
    return None

async def bridge_handler(frontend_ws):
    print("🌐 Cliente Frontend conectado!")
    
    try:
        async with websockets.connect(GEMINI_WS_URL) as gemini_ws:
            # Mensagem de configuração inicial
            setup_message = {
                "setup": {
                    "model": f"models/{MODEL_NAME}",
                    "generationConfig": {
                        "responseModalities": ["AUDIO"]
                    },
                    "systemInstruction": {
                        "parts": [{
                            "text": "Você é um assistente conversacional em tempo real. Responda SEMPRE em Português do Brasil (pt-BR). Use frases curtas e tom natural. Seu nome é Otto."
                        }]
                    }
                }
            }
            await gemini_ws.send(json.dumps(setup_message))
            
            # Confirmação do Gemini
            init_res = await gemini_ws.recv()
            print("⚡ Sessão com Gemini estabelecida com sucesso!")

            # 1. Recebe áudio do navegador e repassa ao Gemini
            async def forward_frontend_to_gemini():
                try:
                    async for message in frontend_ws:
                        msg_data = json.loads(message)
                        if msg_data.get("type") == "audio":
                            sample_rate = msg_data.get("sampleRate", 16000)
                            realtime_payload = {
                                "realtimeInput": {
                                    "mediaChunks": [{
                                        "mimeType": f"audio/pcm;rate={sample_rate}",
                                        "data": msg_data["data"]
                                    }]
                                }
                            }
                            await gemini_ws.send(json.dumps(realtime_payload))
                except websockets.ConnectionClosed:
                    pass

            # 2. Recebe a resposta do Gemini e repassa ao Frontend
            async def forward_gemini_to_frontend():
                try:
                    async for message in gemini_ws:
                        response = json.loads(message)
                        server_content = response.get("serverContent", {})
                        model_turn = server_content.get("modelTurn", {})
                        parts = model_turn.get("parts", [])

                        for part in parts:
                            inline_data = part.get("inlineData", {})
                            if inline_data.get("mimeType", "").startswith("audio/pcm"):
                                await frontend_ws.send(json.dumps({
                                    "type": "audio",
                                    "data": inline_data["data"]
                                }))

                        if server_content.get("turnComplete"):
                            await frontend_ws.send(json.dumps({"type": "turnComplete"}))
                except websockets.ConnectionClosed:
                    pass

            await asyncio.gather(forward_frontend_to_gemini(), forward_gemini_to_frontend())

    except Exception as e:
        print(f"❌ Erro na conexão com o Gemini: {e}")

async def main():
    print("🚀 Servidor Bridge rodando em http://127.0.0.1:8765")
    async with websockets.serve(
        bridge_handler, 
        "0.0.0.0", 
        8765, 
        process_request=process_request
    ):
        await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Servidor encerrado com sucesso!")
