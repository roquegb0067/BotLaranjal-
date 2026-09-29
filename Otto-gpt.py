import os
from dotenv import load_dotenv
from openai import OpenAI

# Carrega as variáveis de ambiente cadastradas no arquivo .env
load_dotenv()
chave_api = os.getenv("OPENAI_API_KEY")

# Inicializa o cliente da OpenAI de forma explícita (Padrão v1.x+)
# Ele busca automaticamente a variável "OPENAI_API_KEY" carregada do arquivo .env
client = OpenAI()

openai.api_key = chave_api

def enviar_mensagem (mensagem):

  resposta = openai.ChatCompletion.create(
  
    model = "gpt-6-astra",
    
    messages = [
      
      {"role": "user", "content": mensagem}
      
    ],
  
  )

  return resposta ["choices"][0]["message"]
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