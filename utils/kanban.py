import os
from pathlib import Path

from config import VAULT_PATH, KANBAN_FILE_REL, KANBAN_HEADER

KANBAN_FILE = Path(VAULT_PATH) / KANBAN_FILE_REL

def _ensure_file():
    """Создаёт kanban‑файл и заголовок, если их ещё нет."""
    if not KANBAN_FILE.exists():
        KANBAN_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(KANBAN_FILE, "w", encoding="utf-8") as f:
            f.write(f"{KANBAN_HEADER}\n\n")

def add_card(note_filename_no_ext: str):
    _ensure_file()
    card_line = f"- [ ] [[{note_filename_no_ext}]]\n"

    with open(KANBAN_FILE, "r+", encoding="utf-8") as f:
        lines = f.readlines()

        # Уже есть?
        if any(card_line.strip() == ln.strip() for ln in lines):
            return

        # Ищем сам заголовок
        try:
            idx = next(
                i for i, ln in enumerate(lines)
                if ln.strip() == KANBAN_HEADER.strip()
            )
        except StopIteration:
            # заголовок отсутствует – добавим в конец
            lines.append(f"{KANBAN_HEADER}\n")
            idx = len(lines) - 1

        # позиция для вставки: сразу после заголовка + возможных пустых строк
        insert_pos = idx + 1
        while insert_pos < len(lines) and lines[insert_pos].strip() == "":
            insert_pos += 1

        lines.insert(insert_pos, card_line)

        # перезаписываем файл
        f.seek(0)
        f.writelines(lines)
        f.truncate()

