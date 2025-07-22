import os
from state import update_last_saved_time
from utils.file_saver import save_attachment, sanitize_filename, save_text_message
from utils.forward import extract_forward_info


async def save_album(messages):
    """messages: list[telegram.Message] с одним media_group_id."""
    caption = next((m.caption for m in messages if m.caption), "")
    links, hints, skipped_notes = [], [], []

    # --- скачиваем / проверяем каждое вложение ---
    for m in messages:
        link, hint, skip = await save_attachment(m)          # ← теперь 3 значения
        if link:        # может быть placeholder ИЛИ ![[Images/...]]
            links.append(link)
        if hint:
            hints.append(hint)
        if skip:        # предупреждение о большом файле
            skipped_notes.append(skip)

    if not links:       # ни одного поддерживаемого вложения
        return

    # --- формируем тело заметки ---
    body_parts = []
    if caption:
        body_parts.append(caption.strip())
    body_parts.extend(links)
    if skipped_notes:
        body_parts.append("\n".join(skipped_notes))

    body = "\n\n".join(body_parts)

    # --- имя файла / заголовок ---
    name_hint = sanitize_filename(caption.splitlines()[0]) if caption else None
    if not name_hint:                                # пусто? ➜ fallback
        name_hint = hints[0] if hints else "album"

    # --- источник пересылки ---
    forwarded = extract_forward_info(messages[0])

    # --- создаём .md файл ---
    md_path = save_text_message(
        messages[0],
        body,
        name_hint=name_hint,
        forwarded_from=forwarded
    )

    # --- ответ‑квитанция ---
    reply_lines = [f"✅ Сохранено альбомом: `{os.path.basename(md_path)}`"]
    if skipped_notes:
        reply_lines.extend(skipped_notes)

    await messages[0].reply_text(
        "\n".join(reply_lines),
        parse_mode="Markdown"
    )

    update_last_saved_time()
