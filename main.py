import logging
import os
from datetime import datetime
from uuid import uuid4
from telegram import Update, MessageEntity
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CommandHandler, filters
from logging.handlers import RotatingFileHandler

from config import BOT_TOKEN, AUTHORIZED_USER_ID, VAULT_PATH
from utils.file_saver import save_text_message, save_attachment
from state import update_last_saved_time, get_last_saved_time, load_state
from utils.forward import extract_forward_info


# Настройка логгера
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

log_formatter = logging.Formatter("%(asctime)s — %(levelname)s — %(message)s")

file_handler = RotatingFileHandler("bot.log", maxBytes=1_000_000, backupCount=3)
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.INFO)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(log_formatter)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    if user_id != AUTHORIZED_USER_ID:
        await update.message.reply_text("🚫 Доступ запрещён.")
        return

    message = update.message
    if not message:
        logging.warning("Обновление не содержит message. Пропущено.")
        return

    forwarded_from = extract_forward_info(message)

    saved_files = []

    media_link = None

    if message.document or message.photo or message.audio or message.video or message.voice:
        media_link = await save_attachment(message)

    if message.text or message.caption:
        text = message.text or message.caption
        if media_link:
            text = f"{text.strip()}\n\n{media_link[0]}"  # добавляем ссылку в конец текста
        file_path = save_text_message(message, text, forwarded_from=forwarded_from)
        saved_files.append(file_path)

    elif media_link:
        file_path = save_text_message(message, text=media_link[0], name_hint=media_link[1], forwarded_from=forwarded_from)
        saved_files.append(file_path)

    # Ответ
    if saved_files:
        update_last_saved_time()
        reply = "✅ Сохранено:\n" + "\n".join(f"- `{os.path.basename(f)}`" for f in saved_files)
        await message.reply_text(reply, parse_mode="Markdown")
    else:
        await message.reply_text("⚠️ Нечего сохранять.")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != AUTHORIZED_USER_ID:
        await update.message.reply_text("🚫 Доступ запрещён.")
        return

    msg = f"📊 *Статус бота:*\n"
    msg += f"👤 Пользователь: `{user_id}`\n"
    msg += f"📁 Vault: `{VAULT_PATH}`\n"
    lst = get_last_saved_time()
    if lst:
        msg += f"🕒 Последнее сохранение: `{lst.strftime('%Y-%m-%d %H:%M:%S')}`"
    else:
        msg += "🕒 Последнее сохранение: _ещё не было_"

    await update.message.reply_text(msg, parse_mode="Markdown")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.error("Произошла ошибка: %s", context.error)


if __name__ == "__main__":
    load_state()
    non_command_filter = filters.TEXT & ~filters.COMMAND

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(MessageHandler(non_command_filter | filters.ATTACHMENT, handle_message))
    app.add_error_handler(error_handler)

    print("🤖 Бот запущен...")
    app.run_polling()
