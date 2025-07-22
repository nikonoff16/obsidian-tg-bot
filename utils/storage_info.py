# utils/storage_info.py
import os
import shutil
from pathlib import Path

from config import VAULT_PATH  # абсолютный путь к хранилищу

def _human_size(num_bytes: int) -> str:
    """Переводит байты в читаемый вид: 1024**n -> KB / MB / GB / TB."""
    step = 1024.0
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    size = float(num_bytes)
    for unit in units:
        if size < step:
            return f"{size:.1f}{unit}"
        size /= step
    return f"{size:.1f}PB"

def get_vault_size() -> int:
    """Подсчитывает размер всех файлов в VAULT_PATH (рекурсивно)."""
    total = 0
    for root, _, files in os.walk(VAULT_PATH):
        for fname in files:
            try:
                total += os.path.getsize(os.path.join(root, fname))
            except (FileNotFoundError, PermissionError):
                pass
    return total

def get_disk_free(path: str | Path = VAULT_PATH) -> int:
    """Возвращает свободное место на диске, где расположен `path` (в байтах)."""
    usage = shutil.disk_usage(Path(path).anchor)
    return usage.free    # также есть usage.total, usage.used

def storage_report(short: bool = True) -> str:
    """Возвращает строку‑отчёт: краткую или развёрнутую."""
    vault_bytes = get_vault_size()
    free_bytes  = get_disk_free(VAULT_PATH)

    vault_str = _human_size(vault_bytes)
    free_str  = _human_size(free_bytes)

    if short:
        return f"{vault_str} / {free_str}"
    return f"Хранилище занимает: {vault_str}\nОставшееся место на диске: {free_str}"
