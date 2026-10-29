import os
from dotenv import load_dotenv
from gigachat import GigaChat
from prompts import SYSTEM_PROMPT
from gigachat.models import ChatCompletionRequest, ChatMessage, ChatModelOptions
load_dotenv()
key = os.getenv("GIGACHAT_CREDENTIALS")
scope = os.getenv("GIGACHAT_SCOPE")
max_pairs = 3
messages=[
    ChatMessage(
        role= "system",
        content=SYSTEM_PROMPT,
    )
]

with open("chat_history.txt", "a", encoding="utf-8") as history_file:
    history_file.write("Новый запуск\n\n")

print("Доступные команды: выход, очистить, история")
print("О чём хотите поговорить?")

while True:
    question = input("Ожидание ввода").strip()
    command = question.lower()
    if command == "выход":
        print("Завершение работы")
        break
    elif command == "очистить":
        confirm = input("Подтвердить? Да/Нет").strip()
        if confirm.lower() == "да":
            messages = messages[0:1]
            print("Очистка завершена")
            with open("chat_history.txt", "a", encoding="utf-8") as history_file:
                history_file.write("История текущего диалога очищена\n\n")
            continue
        else:
            print("Отмена очистки")
            continue
    elif command == "история":
        print(f"Всего сообщений: {len(messages)}")
        print("Порядок ролей:")
        for i in messages:
            print(i.role)
        continue

    messages.append(
        ChatMessage(
            role="user",
            content=question,
        )
    )

    max_messages = 1 + (max_pairs * 2)
    if len(messages) > max_messages:
        messages = [messages[0]] + messages[-(max_messages - 1):]

    request = ChatCompletionRequest(
        messages=messages,
        model_options = ChatModelOptions(
            temperature=0.2,
            max_tokens=400,
            top_p=1,
            repetition_penalty=1.0,
        )
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
    if not question:
        print("Запрос пустой - отправка отменена")
    else:
        answer = response.messages[0].content[0].text
        print("Ответ:")
        print(answer)
        messages.append(
            ChatMessage(
                role="assistant",
                content=answer,
            )
        )
        with open("last_prompt", "w", encoding="utf-8") as file:
            file.write(question)
        with open("last_answer", "w", encoding="utf-8") as file:
            file.write(answer)
        
        with open("chat_history.txt", "a", encoding="utf-8") as history_file:
            history_file.write(f"Вы: {question}\n")
            history_file.write(f"ИИ: {answer}\n\n")
