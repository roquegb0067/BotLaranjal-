import whisper

modelo whisper.load_model("tiny")

resposta = modelo.transcribe("Gravando.m4a")

I

print(resposta)