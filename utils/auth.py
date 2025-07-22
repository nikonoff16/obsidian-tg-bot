import logging
from datetime import datetime, timezone
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes

from config import AUTHORIZED_USER_ID
from utils.notify import notify_owner

def require_auth(handler):
    """
    Декоратор: пускает только AUTHORIZED_USER_ID.
    Иначе логирует, уведомляет владельца, отвечает нарушителю.
    """
    @wraps(handler)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        user_id = user.id if user else None

        if user_id != AUTHORIZED_USER_ID:
            username = user.username or "<no username>"
            logging.warning("НЕАВТОРИЗОВАННЫЙ ДОСТУП: id=%s, user=%s", user_id, username)

            now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            alert = (
                "🚨 *Попытка доступа*\n"
                f"👤 id: `{user_id}`  user: `{username}`\n"
                f"🕒 {now}"
            )
            await notify_owner(context, alert)

            if update.message:
                await update.message.reply_text("🚫 Доступ запрещён.")
            return  # не пускаем дальше

        return await handler(update, context, *args, **kwargs)

    return wrapper
