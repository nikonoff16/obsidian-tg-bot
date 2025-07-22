import logging
import os
import asyncio
from datetime import datetime, timezone
from pathlib import Path

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, CommandHandler, filters, JobQueue, \
    CallbackContext
from logging.handlers import RotatingFileHandler

from config import BOT_TOKEN, AUTHORIZED_USER_ID, VAULT_PATH, BOT_MSG_TTL_SEC, KANBAN_HEADER
from utils.kanban import add_card
from utils.save_album import save_album
from utils.file_saver import save_text_message, save_attachment
from state import update_last_saved_time, get_last_saved_time, load_state
from utils.forward import extract_forward_info
from utils.album_buffer import AlbumBuffer
from utils.storage_info import storage_report


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

async def send_and_auto_delete(orig_msg, text: str,
                               context: ContextTypes.DEFAULT_TYPE,
                               *, parse_mode="Markdown"):
    sent = await orig_msg.reply_text(text, parse_mode=parse_mode)

    if BOT_MSG_TTL_SEC <= 0:
        return

    jq = context.job_queue    # 👉 гарантированно не None

    jq.run_once(
        _delete_message,
        when=BOT_MSG_TTL_SEC,
        data=(sent.chat_id, sent.message_id)
    )

    # сколько прошло секунд с момента отправки пользователя
    msg_age = (datetime.now(timezone.utc) - orig_msg.date).total_seconds()
    if msg_age < BOT_MSG_TTL_SEC:
        jq.run_once(
            _delete_message,
            when=BOT_MSG_TTL_SEC,
            data=(orig_msg.chat_id, orig_msg.message_id)
        )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    album_buffer._context = context
    user_id = update.effective_user.id
    if user_id != AUTHORIZED_USER_ID:
        await update.message.reply_text("🚫 Доступ запрещён.")
        logging.warning(f"ПОПЫТКА ВХОДА ИЗ ПОД НЕАВТОРИЗОВАННОЙ УЧЕТНОЙ ЗАПИСИ: {user_id}")
        return

    message = update.message
    if not message:
        logging.warning("Обновление не содержит message. Пропущено.")
        return

    forwarded_from = extract_forward_info(message)

    saved_files: list[str] = []     # пути созданных md‑файлов
    skipped_notes: list[str] = []   # предупреждения о больших файлах

    # ❶ Альбом — складываем и выходим
    if message.media_group_id:
        album_buffer.add(message, asyncio.get_running_loop())
        return

    # ❷ Одиночное вложение (или его нет)
    media_link, media_hint, skip_note = await save_attachment(message) if (
        message.document or message.photo or message.audio
        or message.video   or message.voice
    ) else (None, None, None)

    if skip_note:
        skipped_notes.append(skip_note)

    # ❸ Текст / caption
    if message.text or message.caption:
        text = message.text or message.caption
        if media_link:
            text = f"{text.strip()}\n\n{media_link}"
        md_path = save_text_message(
            message,
            text,
            forwarded_from=forwarded_from
        )
        saved_files.append(md_path)
        add_card(Path(md_path).stem)

        # ❹ Сообщение без текста, но с вложением
    elif media_link:
        md_path = save_text_message(
            message,
            media_link,
            name_hint=media_hint,
            forwarded_from=forwarded_from
        )
        saved_files.append(md_path)
        # TODO: одиночные файлы без описания не добавляются в канбан

    # ❺ Формируем ответ
    reply_lines: list[str] = []

    if saved_files:
        update_last_saved_time()
        reply_lines.append(
            "✅ Сохранено:\n" +
            "\n".join(f"- `{os.path.basename(p)}`" for p in saved_files)
        )

    if skipped_notes:
        reply_lines.extend(skipped_notes)

    if saved_files:  # ← показываем, только если что‑то сохранилось
        reply_lines.append(f"\n💾 `{storage_report()}`")

    await send_and_auto_delete(update.message,
        "\n".join(reply_lines) or "⚠️ Нечего сохранять.",
        context,
        parse_mode="Markdown"
    )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != AUTHORIZED_USER_ID:
        await update.message.reply_text("🚫 Доступ запрещён.")
        return

    vault_stats = storage_report(short=False)      # "Хранилище занимает: …\nОставшееся место…"

    msg_lines = [
        "📊 *Статус бота:* Alive",
        f"👤 Пользователь: `{user_id}`",
        f"📁 Vault: `{VAULT_PATH}`",
    ]

    last = get_last_saved_time()
    if last:
        msg_lines.append(f"🕒 Последнее сохранение: `{last.strftime('%Y-%m-%d %H:%M:%S')}`")
    else:
        msg_lines.append("🕒 Последнее сохранение: _ещё не было_")

    msg_lines.append("")                # пустая строка‑разделитель
    msg_lines.extend(vault_stats.splitlines())

    await send_and_auto_delete(update.message, "\n".join(msg_lines), context, parse_mode="Markdown")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.error("Произошла ошибка: %s", context.error)

async def _delete_message(context: CallbackContext):
    """Удаляет сообщение, chat_id / msg_id лежат в context.job.data."""
    chat_id, msg_id = context.job.data
    # TODO: если в сообщении было несколько значений (медиагруппа), то удаляется только одно сообщение. Нужно исправить.
    try:
        await context.bot.delete_message(chat_id, msg_id)
    except Exception:
        pass   # сообщение уже удалено или нет прав


if __name__ == "__main__":
    load_state()
    non_command_filter = filters.TEXT & ~filters.COMMAND

    loop = asyncio.get_event_loop()
    album_buffer = AlbumBuffer(cb_save=save_album, timeout=1.0, context=None)

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    job_queue: JobQueue = app.job_queue
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(MessageHandler(non_command_filter | filters.ATTACHMENT, handle_message))
    app.add_error_handler(error_handler)

    print("🤖 Бот запущен...")
    app.run_polling()
