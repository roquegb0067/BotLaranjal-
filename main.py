import io
import wave
import subprocess
import sounddevice as sd
from dotenv import load_dotenv
from google import genai
from google.genai import types
from gtts import gTTS

# Carrega a API Key do arquivo .env
load_dotenv()

# 1. Configurações de Gravação
SAMPLE_RATE = 48000
DURATION = 5

print("🎤 Fale algo! Gravando...")
audio_data = sd.rec(int(DURATION * SAMPLE_RATE), samplerate=SAMPLE_RATE, channel>
sd.wait()
print("✅ Gravação concluída! Processando...")

# 2. Converte a gravação para WAV em memória RAM
wav_buffer = io.BytesIO()
with wave.open(wav_buffer, 'wb') as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(SAMPLE_RATE)
    wf.writeframes(audio_data.tobytes())

wav_bytes = wav_buffer.getvalue()

# 3. Inicializa o cliente definindo um timeout de 30 segundos
# O http_options evita que a requisição fique presa para sempre se houver lentid>
client = genai.Client(
    http_options=types.HttpOptions(timeout=30000)
)

print("🚀 Enviando áudio para o Gemini (gemini-3.5-flash-lite)...")

try:
    response = client.models.generate_content(
        model='gemini-3.5-flash-lite',
        contents=[
            "Responda de forma direta e curta em português ao áudio a seguir:",
            types.Part.from_bytes(
                data=wav_bytes,
                mime_type='audio/wav',
            )
        ]
    )

    resposta_texto = response.text
    print(f"\n🤖 Resposta do Gemini: {resposta_texto}")

    # 4. Sintetiza a resposta em áudio (Text-to-Speech)
    print("🔊 Gerando voz...")
    tts = gTTS(text=resposta_texto, lang='pt', slow=False)

    with open("resposta.mp3", "wb") as f:
        tts.write_to_fp(f)

    # 5. Reproduz o áudio no alto-falante do celular
    print("▶️ Tocando no alto-falante...")
    subprocess.run(["termux-media-player", "play", "resposta.mp3"])

except Exception as e:
    print(f"\n❌ Erro na requisição: {e}")