# Telegram → Obsidian Selfbot

Этот бот сохраняет все входящие сообщения и вложения в Markdown-документы для Obsidian.

## Установка

```bash
git clone ...
cd telegram_selfbot_obsidian
python -m venv venv
source venv/bin/activate  # или venv\Scripts\activate на Windows
pip install -r requirements.txt
```

Создайте .env и укажите в нем:

BOT_TOKEN
AUTHORIZED_USER_ID
VAULT_PATH — абсолютный путь к вашему Obsidian Vault

## Запуск
```bash
python main.py
```

Файлы сохраняются в:

`/Notes` — текстовые сообщения
`/Images` — вложения