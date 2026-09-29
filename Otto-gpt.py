import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI()

def enviar_mensagem(mensagem):

    resposta = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "user",
                "content": mensagem
            }
        ]
    )

    return resposta.choices[0].message.content


while True:
    texto = input("\nEscreva aqui sua mensagem (ou digite 'sair'): ")

    if texto.strip().lower() == "sair":
        print("Encerrando o chat. Até logo!")
        break

    print("Pensando...")

    try:
        resposta_api = enviar_mensagem(texto)
        print(f"Bot: {resposta_api}")

    except Exception as e:
        print(f"Erro na API: {e}")