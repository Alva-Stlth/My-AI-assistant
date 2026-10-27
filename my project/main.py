import os
from dotenv import load_dotenv
from gigachat import GigaChat
from prompts import SYSTEM_PROMPT
from gigachat.models import ChatCompletionRequest, ChatMessage
load_dotenv()
key = os.getenv("GIGACHAT_CREDENTIALS")
scope = os.getenv("GIGACHAT_SCOPE")
question = input("О чём хотите поговорить?").strip()
request = ChatCompletionRequest(
    messages=[
        ChatMessage(
            role= "system",
            content=SYSTEM_PROMPT,
        ),
        ChatMessage(
            role="user",
            content=question,
        )
    ]
)
print("Отправляем запрос")
with GigaChat(
    credentials=key,
    scope=scope,
    model="Gigachat-2",
    ca_bundle_file="certs/russian_trusted_root_ca_pem.crt",
    timeout=60,
) as client:
    response = client.chat.create(request)
answer = response.messages[0].content[0].text
print("Ответ:")
print(answer)