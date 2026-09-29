import whisper

# Adicionado o sinal de = aqui para corrigir o erro
modelo = whisper.load_model("tiny")

# Configurado para transcrever direto em português e rodar liso na CPU do celular
resposta = modelo.transcribe("Gravando2.m4a", language="pt", fp16=False)

print(resposta["text"])
