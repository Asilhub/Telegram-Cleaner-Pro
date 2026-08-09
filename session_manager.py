import os
import asyncio
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from telethon import TelegramClient
from telethon.errors import (
    SessionPasswordNeededError,
    PhoneCodeInvalidError,
    PhoneNumberInvalidError,
    PasswordHashInvalidError
)
from config import SESSIONS_DIR, get_api_credentials, save_api_credentials

class SessionManager:
    def __init__(self):
        self.sessions_dir = SESSIONS_DIR
        self.sessions_dir.mkdir(exist_ok=True)

    def list_sessions(self) -> List[Path]:
        """Mavjud barcha .session fayllar ro'yxatini qaytaradi"""
        return sorted(list(self.sessions_dir.glob("*.session")))

    def get_client(self, session_name: str, api_id: int, api_hash: str) -> TelegramClient:
        """Sessiya nomi bo'yicha TelegramClient ob'ektini yaratadi"""
        session_path = self.sessions_dir / session_name
        return TelegramClient(str(session_path), api_id, api_hash)

    async def get_account_info(self, client: TelegramClient) -> Optional[Dict]:
        """Uланган hisob haqida to'liq ma'lumotni oladi"""
        try:
            if not client.is_connected():
                await client.connect()
            if not await client.is_user_authorized():
                return None
            me = await client.get_me()
            return {
                "id": me.id,
                "first_name": me.first_name or "",
                "last_name": me.last_name or "",
                "username": f"@{me.username}" if me.username else "Mavjud emas",
                "phone": f"+{me.phone}" if me.phone else "Yashirin",
                "premium": getattr(me, 'premium', False),
            }
        except Exception as e:
            return {"error": str(e)}

    async def load_all_accounts_info(self, api_id: int, api_hash: str) -> List[Dict]:
        """Barcha mavjud .session fayllarining hisob ma'lumotlarini yuklaydi"""
        sessions = self.list_sessions()
        accounts = []
        for session_file in sessions:
            session_name = session_file.stem
            client = self.get_client(session_name, api_id, api_hash)
            try:
                await client.connect()
                is_auth = await client.is_user_authorized()
                if is_auth:
                    info = await self.get_account_info(client)
                    if info:
                        info["session_name"] = session_name
                        info["session_file"] = session_file.name
                        accounts.append(info)
                else:
                    accounts.append({
                        "session_name": session_name,
                        "session_file": session_file.name,
                        "error": "Sessiya faol emas (Qayta login kerak)"
                    })
            except Exception as e:
                accounts.append({
                    "session_name": session_name,
                    "session_file": session_file.name,
                    "error": str(e)
                })
            finally:
                if client.is_connected():
                    await client.disconnect()
        return accounts

    def delete_session(self, session_name: str) -> bool:
        """Sessiya faylini o'chirish"""
        session_path = self.sessions_dir / f"{session_name}.session"
        if session_path.exists():
            session_path.unlink()
            return True
        return False
