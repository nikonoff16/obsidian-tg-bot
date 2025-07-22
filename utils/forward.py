# utils/forward.py
from typing import Optional
from telegram import Message

def extract_forward_info(msg: Message) -> Optional[str]:
    """Возвращает строку‑источник или None, если сообщение не переслано."""
    # 1) Пользователь
    if getattr(msg, "forward_from", None):
        u = msg.forward_from
        return f"@{u.username}" if u.username else f"{u.full_name}".strip()

    # 2) Канал / группа
    if getattr(msg, "forward_from_chat", None):
        ch = msg.forward_from_chat
        return ch.title or f"@{ch.username}" if ch.username else "Unknown channel"

    # 3) Скрытый пользователь
    if getattr(msg, "forward_sender_name", None):
        return msg.forward_sender_name          # уже готовая строка

    # 4) Новое поле forward_origin (Bot API ≥ 6.7)
    origin = getattr(msg, "forward_origin", None)
    if origin:
        if hasattr(origin, "sender_user"):
            u = origin.sender_user
            return f"@{u.username}" if u.username else u.full_name
        if hasattr(origin, "chat"):
            return origin.chat.title or origin.chat.username
        if hasattr(origin, "sender_name"):
            return origin.sender_name

    # 5) Просто отметим факт пересылки
    if getattr(msg, "forward_date", None):
        return "Unknown source"

    return None
