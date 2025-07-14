import os, re
import uuid
from datetime import datetime
from config import NOTES_DIR, IMAGES_DIR
from utils.formatter import format_markdown_note
from uuid import uuid4

def sanitize_filename(s: str) -> str:
    """
    Удаляет или заменяет все символы, которые нельзя использовать в имени файла.
    Заменяет пробелы и спецсимволы на подчёркивания.
    """
    # Убираем запрещённые символы и заменяем пробельные символы на _
    s = re.sub(r'[\\/:*?"<>|]', '', s)           # Удаляем опасные символы
    s = re.sub(r'\s+', '_', s)                   # Пробелы и табы → _
    s = re.sub(r'[_]+', '_', s)                  # Сжимаем повторяющиеся подчёркивания
    return s.strip('_')[:60]                     # Усечение до 60 символов и обрезка по краям

def get_filename_prefix(message):
    dt = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    return dt


def save_text_message(message, text: str, name_hint: str = None) -> str:
    if name_hint:
        base = name_hint
    else:
        base = text.strip().splitlines()[0][:60]
    first_line = text.strip().splitlines()[0][:60]
    safe_line = sanitize_filename(base)
    unique_id = uuid.uuid4().hex
    base_name = f"{unique_id}_{safe_line}.md"
    file_title = base_name[:-3]

    content = format_markdown_note(title=file_title, created=datetime.now(), body=text)
    path = os.path.join(NOTES_DIR, base_name)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path

async def save_attachment(message) -> tuple[str, str]:
    dt = datetime.now()
    prefix = get_filename_prefix(message)

    # Определяем файл и расширение
    if message.document:
        file = await message.document.get_file()
        filename = message.document.file_name
    elif message.photo:
        file = await message.photo[-1].get_file()
        filename = f"{prefix}_photo.jpg"
    elif message.audio:
        file = await message.audio.get_file()
        filename = message.audio.file_name or f"{prefix}_audio.mp3"
    elif message.video:
        file = await message.video.get_file()
        filename = message.video.file_name or f"{prefix}_video.mp4"
    elif message.voice:
        file = await message.voice.get_file()
        filename = f"{prefix}_voice.ogg"
    else:
        return None

    unique_id = uuid.uuid4().hex
    name_part = sanitize_filename(filename.rsplit(".", 1)[0])
    ext = filename.rsplit(".", 1)[-1].lower()
    safe_name = f"{unique_id}_{name_part}.{ext}"

    full_path = os.path.join(IMAGES_DIR, safe_name)
    await file.download_to_drive(full_path)

    return f"![[Images/{safe_name}]]", name_part


