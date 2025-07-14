import json
from datetime import datetime
from pathlib import Path

STATE_FILE = Path("state.json")
_last_saved_time: datetime | None = None

def load_state():
    global _last_saved_time
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "last_saved_time" in data:
                    _last_saved_time = datetime.fromisoformat(data["last_saved_time"])
        except Exception as e:
            print(f"⚠️ Не удалось загрузить состояние: {e}")

def save_state():
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "last_saved_time": _last_saved_time.isoformat() if _last_saved_time else None
            }, f, indent=2)
    except Exception as e:
        print(f"⚠️ Не удалось сохранить состояние: {e}")

def update_last_saved_time():
    global _last_saved_time
    _last_saved_time = datetime.now()
    save_state()

def get_last_saved_time() -> datetime | None:
    return _last_saved_time