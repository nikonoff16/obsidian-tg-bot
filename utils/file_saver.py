# utils/file_saver.py
import os
import re
import uuid
from datetime import datetime

# Внешние зависимости проекта
from telegram import Message, File            # типы удобны для IDE, не обязательны

# Локальные модули
from config import NOTES_DIR, IMAGES_DIR, MAX_ATTACHMENT_BYTES, MAX_ATTACHMENT_MB
from utils.formatter import format_markdown_note


# characters disallowed on most OS: \ / : * ? " < > | #
_ILLEGAL = r'[\\/:*?"<>|#\x00-\x1F]'

def timestamp_prefix() -> str:
    """Возвращает строку вида 20250722-151630."""
    return datetime.now().strftime("%Y%m%d-%H%M%S")

def sanitize_filename(name: str, max_len: int = 60) -> str:
    """
    Делает строку безопасной для использования как имя файла.
    - запрещённые символы (\ / : * ? " < > | # и управляющие) удаляются
    - пробелы/табы -> '_'
    - повторяющиеся '_' сжимаются
    - усечение до max_len символов
    """
    clean = re.sub(_ILLEGAL, '', name)       # убираем опасные
    clean = re.sub(r'\s+', '_', clean)       # пробелы -> _
    clean = re.sub(r'[_]+', '_', clean)      # подряд '_' -> одна
    clean = clean.strip('_')                 # по краям не нужны
    return clean[:max_len]                   # ограничиваем длину

# ---------- текстовое сообщение ----------

def save_text_message(message, text: str, name_hint: str | None = None,
                      forwarded_from: str | None = None) -> str:
    slug_base = name_hint or text.strip().splitlines()[0][:60]
    slug = sanitize_filename(slug_base) or uuid.uuid4().hex[:8]
    fname     = f"{timestamp_prefix()}_{slug or uuid.uuid4().hex}.md"
    # если slug после чистки пустой, страхуемся UUID‑ом
    file_title = fname[:-3]

    content = format_markdown_note(
        title=file_title,
        created=datetime.now(),
        body=text,
        forwarded_from=forwarded_from
    )
    path = os.path.join(NOTES_DIR, fname)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path

# ---------- вложение ----------

# utils/file_saver.py  (фрагмент)

async def save_attachment(message):
    """
    Возвращает кортеж:
      markdown_line  – строка, которую нужно вставить в заметку
      name_hint      – slug без расширения (для title)
      skip_info      – None | текст предупреждения для отбивки
    """

    # 1️⃣  определяем объект файла и его имя / размер
    if message.document:
        src = message.document
        tg_file = await src.get_file()
        orig_name = src.file_name
        size = src.file_size
    elif message.photo:
        src = message.photo[-1]
        tg_file = await src.get_file()
        orig_name = f"photo_{tg_file.file_id[-6:]}.jpg"
        size = src.file_size
    elif message.audio:
        src = message.audio
        tg_file = await src.get_file()
        orig_name = src.file_name or "audio.mp3"
        size = src.file_size
    elif message.video:
        src = message.video
        tg_file = await src.get_file()
        orig_name = src.file_name or "video.mp4"
        size = src.file_size
    elif message.voice:
        src = message.voice
        tg_file = await src.get_file()
        orig_name = "voice.ogg"
        size = src.file_size
    else:
        return None, None, None          # неизвестный тип

    # 2️⃣  если файл крупнее лимита — не скачиваем
    if size > MAX_ATTACHMENT_BYTES:
        mb = size / 1048576
        placeholder = (
            f"**`{orig_name}` "
            f"({mb:.1f} MB > {MAX_ATTACHMENT_MB:.0f} MB, не сохранено)**"
        )
        skip_note = (
            f"⚠️ Пропущено: `{orig_name}` "
            f"({mb:.1f} MB > {MAX_ATTACHMENT_MB:.0f} MB)"
        )

        hint        = sanitize_filename(orig_name.rsplit('.', 1)[0])
        return placeholder, hint, skip_note

    # 3️⃣  иначе сохраняем, как раньше
    ext = orig_name.rsplit('.', 1)[-1].lower()
    base_slug = sanitize_filename(orig_name.rsplit('.', 1)[0])
    fname = f"{timestamp_prefix()}_{base_slug}.{ext}"
    full_path = os.path.join(IMAGES_DIR, fname)
    await tg_file.download_to_drive(full_path)

    markdown_link = f"![[Images/{fname}]]"
    return markdown_link, base_slug, None

