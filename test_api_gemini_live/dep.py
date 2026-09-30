import asyncio
import websockets
import json
import base64
import os
import struct
import math
import time
import traceback
import pyaudio

p = pyaudio.PyAudio()

# ============================================================
# CONFIGURAÇÃO
# ============================================================

API_KEY = os.environ.get("GEMINI_API_KEY")

#MODEL_NAME = "gemini-3.8-live"
MODEL_NAME = "gemini-2.0-flash-exp"

WS_URL = (
    "wss://generativelanguage.googleapis.com/"
    "ws/google.ai.generativelanguage.v1beta."
    f"GenerativeService.BidiGenerateContent?key={API_KEY}"
)

INPUT_RATE = 16000
OUTPUT_RATE = 24000

CHANNELS = 1
FORMAT = pyaudio.paInt16
CHUNK_SIZE = 1024


# ============================================================
# UTILITÁRIOS
# ============================================================

def ok(msg):
    print(f"✅ {msg}")


def fail(msg):
    print(f"❌ {msg}")


def info(msg):
    print(f"ℹ️ {msg}")


def section(msg):
    print()
    print("=" * 60)
    print(msg)
    print("=" * 60)


# ============================================================
# TESTE 1 — API KEY
# ============================================================

def test_api_key():

    section("TESTE 1 — API KEY")

    if not API_KEY:
        fail("GEMINI_API_KEY não está configurada.")
        return False

    ok("GEMINI_API_KEY encontrada.")
    ok(f"Tamanho da chave: {len(API_KEY)} caracteres")

    return True


# ============================================================
# TESTE 2 — PYAUDIO
# ============================================================

def test_pyaudio_devices(p):

    section("TESTE 2 — DISPOSITIVOS DE ÁUDIO")

    try:
        count = p.get_device_count()

        ok(f"PyAudio encontrou {count} dispositivos.")

        for i in range(count):

            info_device = p.get_device_info_by_index(i)

            print()
            print(f"🎧 DEVICE {i}")
            print(f"   Nome: {info_device['name']}")
            print(f"   Entrada: {info_device['maxInputChannels']}")
            print(f"   Saída: {info_device['maxOutputChannels']}")
            print(f"   Sample rate: {info_device['defaultSampleRate']}")

        return True

    except Exception as e:

        fail(f"Erro ao listar dispositivos: {e}")
        traceback.print_exc()

        return False


# ============================================================
# TESTE 3 — MICROFONE
# ============================================================

def test_microphone(p):

    section("TESTE 3 — MICROFONE")

    stream = None

    try:

        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=INPUT_RATE,
            input=True,
            frames_per_buffer=CHUNK_SIZE
        )

        ok("Microfone abriu.")

        print("🎤 Capturando 2 segundos...")

        frames = []

        for _ in range(
            int(INPUT_RATE / CHUNK_SIZE * 2)
        ):

            data = stream.read(
                CHUNK_SIZE,
                exception_on_overflow=False
            )

            frames.append(data)

        audio = b"".join(frames)

        if len(audio) == 0:

            fail("Nenhum byte capturado.")
            return False

        ok(f"Capturados {len(audio)} bytes.")

        # Mede volume aproximado
        samples = struct.unpack(
            "<" + "h" * (len(audio) // 2),
            audio
        )

        peak = max(abs(x) for x in samples)

        print(f"🎤 Pico do sinal: {peak}")

        if peak == 0:
            fail("Microfone abriu, mas está entregando silêncio.")
        else:
            ok("Microfone está produzindo sinal.")

        return True

    except Exception as e:

        fail(f"Erro no microfone: {e}")
        traceback.print_exc()

        return False

    finally:

        if stream:

            stream.stop_stream()
            stream.close()


# ============================================================
# TESTE 4 — SAÍDA DE ÁUDIO
# ============================================================

def test_speaker(p):

    section("TESTE 4 — SAÍDA DE ÁUDIO")

    stream = None

    try:

        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=OUTPUT_RATE,
            output=True,
            frames_per_buffer=CHUNK_SIZE
        )

        ok("Saída de áudio abriu.")

        print("🔊 Reproduzindo tom de teste por 2 segundos...")

        duration = 2

        frames = []

        frequency = 440

        for i in range(
            int(OUTPUT_RATE * duration)
        ):

            value = int(
                12000 *
                math.sin(
                    2 * math.pi *
                    frequency *
                    i /
                    OUTPUT_RATE
                )
            )

            frames.append(
                struct.pack("<h", value)
            )

        stream.write(b"".join(frames))

        ok("PyAudio enviou o tom.")

        print()
        print("👉 Você deveria ter ouvido um tom de 440 Hz.")
        print("👉 Se não ouviu, o problema pode estar na saída/Bluetooth.")

        return True

    except Exception as e:

        fail(f"Erro no speaker: {e}")
        traceback.print_exc()

        return False

    finally:

        if stream:

            stream.stop_stream()
            stream.close()


# ============================================================
# TESTE 5 — WEBSOCKET
# ============================================================

async def test_websocket():

    section("TESTE 5 — WEBSOCKET")

    try:

        websocket = await websockets.connect(
            WS_URL,
            open_timeout=10
        )

        ok("WebSocket conectado.")

        return websocket

    except Exception as e:

        fail(f"Falha no WebSocket: {e}")
        traceback.print_exc()

        return None


# ============================================================
# TESTE 6 — SETUP GEMINI
# ============================================================

async def test_setup(websocket):

    section("TESTE 6 — SETUP GEMINI")

    setup_message = {
        "setup": {
            "model": f"models/{MODEL_NAME}",
            "generationConfig": {
                "responseModalities": [
                    "AUDIO"
                ]
            }
        }
    }

    try:
        # PRIMEIRO FRAME: obrigatoriamente setup
        await websocket.send(json.dumps(setup_message))

        ok("Mensagem de setup enviada.")

        message = await asyncio.wait_for(
            websocket.recv(),
            timeout=10
        )

        response = json.loads(message)

        print(
            json.dumps(
                response,
                indent=2,
                ensure_ascii=False
            )
        )

        if "setupComplete" in response:
            ok("Gemini confirmou setup.")
            return True

        if "error" in response:
            fail("Gemini retornou erro.")
            return False

        info("Resposta inesperada.")
        return True

    except Exception as e:
        fail(f"Erro no setup: {e}")
        traceback.print_exc()
        return False
# ============================================================
# TESTE 7 — ENVIO DE ÁUDIO
# ============================================================

async def test_send_audio(websocket):
    mic_stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=INPUT_RATE,
        input=True,
        frames_per_buffer=CHUNK_SIZE
    )

    print("✅ Microfone aberto para teste Live.")
    print("🎤 Fale alguma coisa durante os próximos 3 segundos...")

    try:
        # Envia ~3 segundos de áudio
        for _ in range(46):
            data = await asyncio.to_thread(
                mic_stream.read,
                CHUNK_SIZE,
                exception_on_overflow=False
            )

            encoded_data = base64.b64encode(data).decode("utf-8")

            # Estrutura correta: mediaChunks (array)
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

        # Sinaliza explicitamente ao Gemini que a fala terminou
        end_turn_message = {
            "clientContent": {
                "turnComplete": True
            }
        }
        await websocket.send(json.dumps(end_turn_message))

        print("✅ 46 chunks e sinal de 'turnComplete' enviados com sucesso.")

    finally:
        mic_stream.stop_stream()
        mic_stream.close()

# ============================================================
# TESTE 8 — ESCUTAR GEMINI
# ============================================================

async def listen_gemini(websocket, p):

    section("TESTE 8 — RESPOSTAS DO GEMINI")

    speaker_stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=OUTPUT_RATE,
        output=True,
        frames_per_buffer=1024
    )

    audio_received = False

    try:

        while True:

            try:
                message = await asyncio.wait_for(
                    websocket.recv(),
                    timeout=5
                )

            except asyncio.TimeoutError:
                info("5 segundos sem mensagem.")
                continue

            except Exception as e:
                fail(f"WebSocket encerrado: {e}")
                break

            response = json.loads(message)

            print("\n📩 EVENTO:")
            print(json.dumps(
                response,
                indent=2,
                ensure_ascii=False
            ))

            # ==========================================
            # ERRO
            # ==========================================

            if "error" in response:

                fail("GEMINI RETORNOU ERRO")

                print(json.dumps(
                    response["error"],
                    indent=2,
                    ensure_ascii=False
                ))

                break

            # ==========================================
            # SERVER CONTENT
            # ==========================================

            if "serverContent" in response:

                server_content = response["serverContent"]

                print("🧠 SERVER CONTENT RECEBIDO")

                # --------------------------------------
                # MODEL TURN
                # --------------------------------------

                model_turn = server_content.get(
                    "modelTurn",
                    {}
                )

                parts = model_turn.get(
                    "parts",
                    []
                )

                for part in parts:

                    print("📦 PART:")
                    print(json.dumps(
                        part,
                        indent=2,
                        ensure_ascii=False
                    ))

                    inline_data = part.get(
                        "inlineData"
                    )

                    if not inline_data:
                        continue

                    mime_type = inline_data.get(
                        "mimeType",
                        ""
                    )

                    if mime_type.startswith("audio/pcm"):

                        audio_bytes = base64.b64decode(
                            inline_data["data"]
                        )

                        print(
                            f"🔊 ÁUDIO RECEBIDO: "
                            f"{len(audio_bytes)} bytes"
                        )

                        speaker_stream.write(
                            audio_bytes
                        )

                        audio_received = True

                # --------------------------------------
                # TURN COMPLETE
                # --------------------------------------

                if server_content.get(
                    "turnComplete"
                ):

                    print("✅ TURN COMPLETE")

                    break

    finally:

        speaker_stream.stop_stream()
        speaker_stream.close()

    if audio_received:

        print("\n🎉 Gemini enviou áudio!")

    else:

        print("\n❌ Nenhum áudio recebido.")
# ============================================================
# MAIN
# ============================================================

async def main():

    print()
    print("🧪 GEMINI LIVE AUDIO DIAGNOSTIC")
    print("================================")
    print()

    # --------------------------------------------------------
    # API
    # --------------------------------------------------------

    if not test_api_key():

        return

    # --------------------------------------------------------
    # PYAUDIO
    # --------------------------------------------------------

    try:

        test_pyaudio_devices(p)

        test_microphone(p)

        test_speaker(p)

        # ----------------------------------------------------
        # WEBSOCKET
        # ----------------------------------------------------

        websocket = await test_websocket()

        if not websocket:

            return

        try:

            setup_ok = await test_setup(
                websocket
            )

            if not setup_ok:

                return

            # ------------------------------------------------
            # IMPORTANTE:
            # Depois do setup, testa envio.
            # ------------------------------------------------

            await test_send_audio(
                websocket,
              
            )

            # ------------------------------------------------
            # Agora espera resposta.
            # ------------------------------------------------

            await listen_gemini(
                websocket,
                p
            )

        finally:

            await websocket.close()

    finally:
        p.terminate()
    section("DIAGNÓSTICO FINAL")

    print()
    print("Se aparecer:")
    print()
    print("🔊 ÁUDIO RECEBIDO")
    print()
    print("→ Gemini está enviando voz.")
    print("→ O problema provavelmente é saída/Bluetooth.")
    print()
    print("Se aparecer:")
    print()
    print("❌ GEMINI RETORNOU ERRO")
    print()
    print("→ O problema está na configuração/API.")
    print()
    print("Se não aparecer áudio nem erro:")
    print()
    print("→ precisamos investigar o formato do")
    print("  realtimeInput / modelo Live.")


# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Encerrado pelo usuário.")
    finally:
        p.terminate()
        print()
        print("💥 ERRO FATAL:")
        traceback.print_exc()