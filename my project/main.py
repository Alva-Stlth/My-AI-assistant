import os
from pathlib import Path
from dotenv import load_dotenv
from gigachat import GigaChat
from prompts import SYSTEM_PROMPT
from gigachat.models import ChatCompletionRequest, ChatMessage, ChatModelOptions
import logging
load_dotenv()
key = os.getenv("GIGACHAT_CREDENTIALS")
scope = os.getenv("GIGACHAT_SCOPE")
max_pairs = 3

def clean_text(text):
    lines = text.splitlines()
    clean_lines = []
    for line in lines:
        line = line.strip()
        if line != "":
            clean_lines.append(line)
    return "\n".join(clean_lines)

def clean_line(line):
    line = line.replace("\u00a0", " ")
    line = line.replace("\t", " ")
    line = " ".join(line.split())
    return line

def unique_lines(line):
    unique_lines = []
    for line in line:
        if line not in unique_lines:
            unique_lines.append(line)
    return unique_lines

def normalize_text(text):
    lines = text.splitlines()
    clean_lines = []
    for line in lines:
        line = clean_line(line)
        if line == "":
            continue
        if line not in clean_lines:
            clean_lines.append(line)
    final_unique = unique_lines(clean_lines)
    return "\n".join(final_unique)

def split_with_overlap(text, chunk_size, overlap, minimum_length = 30):
    if chunk_size <= 0:
        raise ValueError("chunk_size должен быть больше 0")
    if overlap < 0:
        raise ValueError("overlap не может быть отрицательным")
    if overlap >= chunk_size:
        raise ValueError("overlap должен быть меньше chunk_size")
    chunks = []
    step = chunk_size - overlap
    for start in range(0, len(text), step):
        chunk = text[start:start + chunk_size].strip()
        if len(chunk) >= minimum_length:
            chunks.append(chunk)
    return chunks

source_dir = Path("normalized")
chunks_dir = Path("chunks")
chunks_dir.mkdir(exist_ok=True)
source_dir = Path("cleaned")
normalized_dir = Path("normalized")
normalized_dir.mkdir(exist_ok=True)
corpus_dir = Path("corpus")
cleaned_dir = Path("cleaned")
cleaned_dir.mkdir(exist_ok=True)
files = list(corpus_dir.glob("*.txt"))
all_chunks = []
documents = []

for file_path in files:
    text = file_path.read_text(encoding="utf-8")
    chunks = split_with_overlap(text, 300, 50)
    for chunk_id, chunk in enumerate(chunks):
        data = {
            "source": file_path.name,
            "chunk_id": chunk_id,
            "text": chunk
        }
        all_chunks.append(data)
        source_stem = file_path.stem
        filename = f"{source_stem}_chunk_{chunk_id}.txt"
        output_path = chunks_dir / filename
        output_path.write_text(chunk, encoding="utf-8")

normalized_files = list(cleaned_dir.glob("*.txt"))

for file_path in normalized_files:
    text = file_path.read_text(encoding="utf-8")
    normalized = normalize_text(text)
    output_path = normalized_dir / file_path.name
    output_path.write_text(normalized, encoding="utf-8")

for file_path in files:
    text = file_path.read_text(encoding="utf-8")
    text = clean_text(text)
    if text == "":
        continue
    documents.append({
        "source": file_path.name,
        "text": text
    })
    output_path = cleaned_dir/file_path.name
    output_path.write_text(text, encoding="utf-8")


messages=[
    ChatMessage(
        role= "system",
        content=SYSTEM_PROMPT,
    )
]

chunk_files = Path("chunks").glob("*.txt")
if chunk_files:
    context = "\n\n---\n\n".join(f.read_text(encoding="utf-8") for f in chunk_files)
    messages.append(ChatMessage(role="user", content=f"Контекст из файлов:\n{context}"))

logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logging.info("Старт программы")

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
    try:
        logging.info("Отправка запроса")
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
            logging.warning("Пустой ввод")
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
            with open("chat_history.txt", "a", encoding="utf-8") as history_file:
                history_file.write(f"Вы: {question}\n")
                history_file.write(f"ИИ: {answer}\n\n")
            logging.info("Ответ успешно получен")
    except Exception as error:
        print("Ошибка обращения к модели")
        logging.error("Ошибка: %s", error)