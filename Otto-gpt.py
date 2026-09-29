import os
from dotenv import load_dotenv
from openai import OpenAI

# Carrega as variáveis de ambiente cadastradas no arquivo .env
load_dotenv()

# Inicializa o cliente da OpenAI de forma explícita (Padrão v1.x+)
# Ele busca automaticamente a variável "OPENAI_API_KEY" carregada do arquivo .env
client = OpenAI()

def enviar_mensagem(mensagem):
    # Usando a nova sintaxe client.chat.completions.create
    resposta = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": mensagem}
        ]
    )
    # Forma correta de extrair o texto na versão atualizada da biblioteca
    return resposta.choices[0].message.content

# Loop principal do chatbot de terminal
while True:
    texto = input("\nEscreva aqui sua mensagem (ou digite 'sair'): ")
    
    # Validação para encerrar o programa corretamente
    if texto.strip().lower() == "sair":
        print("Encerrando o chat. Até logo!")
        break
        
    # Envia o texto digitado pelo usuário dinamicamente
    print("Pensando...")
    resposta_api = enviar_mensagem(texto)
    print(f"Bot: {resposta_api}")
