import os
from dotenv import load_dotenv
from google import genai

load_dotenv("kei.env")

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

def transcrever_audio(caminho):

    arquivo = client.files.upload(
        file=caminho
    )

    resposta = client.interactions.create(
        model="gemini-3.5-transcribe",
        input=[
            {
                "type": "audio",
                "uri": arquivo.uri,
                "mime_type": arquivo.mime_type
            }
        ]
    )

    return resposta.output_text


texto = transcrever_audio("audio.wav")

print(texto)