import os
from pathlib import Path
from dotenv import load_dotenv

# Asosiy yo'llar
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
SESSIONS_DIR = BASE_DIR / "sessions"

# Sessions papkasini avtomatik yaratish
SESSIONS_DIR.mkdir(exist_ok=True)

# .env faylni yuklash
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)

# Standart Telegram API (Foydalanuvchilar my.telegram.org ga kirmasdan to'g'ridan-to'g'ri ishlatishi uchun)
DEFAULT_API_ID = 23026017
DEFAULT_API_HASH = "5787f37be3c717ea375c9e440a848391"

def get_api_credentials():
    """API ma'lumotlarini olish (.env bo'lsa undan, bo'lmasa standartidan)"""
    api_id_env = os.getenv("TELEGRAM_API_ID", "").strip()
    api_hash_env = os.getenv("TELEGRAM_API_HASH", "").strip()
    
    if api_id_env and api_hash_env:
        try:
            return int(api_id_env), api_hash_env
        except ValueError:
            pass
            
    return DEFAULT_API_ID, DEFAULT_API_HASH

def save_api_credentials(api_id: int, api_hash: str):
    """API_ID va API_HASH ni .env fayliga saqlash"""
    lines = []
    if ENV_PATH.exists():
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
    updated_id = False
    updated_hash = False
    new_lines = []
    
    for line in lines:
        if line.startswith("TELEGRAM_API_ID="):
            new_lines.append(f"TELEGRAM_API_ID={api_id}\n")
            updated_id = True
        elif line.startswith("TELEGRAM_API_HASH="):
            new_lines.append(f"TELEGRAM_API_HASH={api_hash}\n")
            updated_hash = True
        else:
            new_lines.append(line)
            
    if not updated_id:
        new_lines.append(f"TELEGRAM_API_ID={api_id}\n")
    if not updated_hash:
        new_lines.append(f"TELEGRAM_API_HASH={api_hash}\n")
        
    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
        
    os.environ["TELEGRAM_API_ID"] = str(api_id)
    os.environ["TELEGRAM_API_HASH"] = str(api_hash)

def get_delete_delay() -> float:
    try:
        return float(os.getenv("DELETE_DELAY_SECONDS", "1.2"))
    except ValueError:
        return 1.2

def get_revoke_for_all() -> bool:
    val = os.getenv("REVOKE_FOR_ALL", "True").strip().lower()
    return val in ("true", "1", "yes", "t")

def get_whitelist() -> set:
    raw = os.getenv("WHITELIST", "")
    items = set()
    for item in raw.split(","):
        cleaned = item.strip().lower()
        if cleaned:
            if cleaned.isdigit() or (cleaned.startswith("-") and cleaned[1:].isdigit()):
                items.add(int(cleaned))
            items.add(cleaned)
    return items
