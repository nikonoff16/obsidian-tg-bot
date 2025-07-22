from telegram.ext import ContextTypes
from config import AUTHORIZED_USER_ID

async def notify_owner(context: ContextTypes.DEFAULT_TYPE, text: str):
    """Шлёт сообщение владельцу (не удаляется)."""
    await context.bot.send_message(chat_id=AUTHORIZED_USER_ID, text=text, parse_mode="Markdown")
