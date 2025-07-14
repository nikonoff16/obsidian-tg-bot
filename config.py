import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
AUTHORIZED_USER_ID = int(os.getenv("AUTHORIZED_USER_ID"))
VAULT_PATH = os.getenv("VAULT_PATH")

NOTES_DIR = os.path.join(VAULT_PATH, "Notes")
IMAGES_DIR = os.path.join(VAULT_PATH, "Images")

os.makedirs(NOTES_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)
