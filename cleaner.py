import asyncio
import time
import logging
from enum import Enum
from datetime import datetime, timezone
from typing import List, Dict, Callable, Optional, Set, Tuple
from telethon import TelegramClient
from telethon.tl import types, functions
from telethon.errors import FloodWaitError, RPCError
from config import get_delete_delay, get_revoke_for_all, get_whitelist

logger = logging.getLogger("cleaner")

Tuple_Result = Tuple[bool, str]

class CleanupMode(Enum):
    JOINED_ONLY = "joined_only"          # Faqat "Telegramga qo'shildi" chatlari
    EMPTY_AND_JOINED = "empty_and_joined"  # Bo'sh chatlar (0 ta xabar) + "Telegramga qo'shildi"
    ALL_SINGLE_MESSAGE = "all_single_msg"  # Faqat 1 ta xabar bo'lgan barcha nofaol chatlar

class ChatTarget:
    def __init__(self, dialog, entity, reason: str, message_count: int, last_message_text: str = ""):
        self.dialog = dialog
        self.entity = entity
        self.id = entity.id
        self.name = dialog.name or f"User_{entity.id}"
        self.username = f"@{entity.username}" if getattr(entity, 'username', None) else ""
        self.phone = f"+{entity.phone}" if getattr(entity, 'phone', None) else ""
        self.reason = reason
        self.message_count = message_count
        self.last_message_text = last_message_text

    def __repr__(self):
        return f"<ChatTarget {self.name} (ID: {self.id}) - {self.reason}>"

class BotTarget:
    def __init__(self, dialog, entity, last_date: Optional[datetime], days_inactive: int, months_inactive: float):
        self.dialog = dialog
        self.entity = entity
        self.id = entity.id
        self.name = dialog.name or f"Bot_{entity.id}"
        self.username = f"@{entity.username}" if getattr(entity, 'username', None) else "Mavjud emas"
        self.last_date = last_date
        self.days_inactive = days_inactive
        self.months_inactive = months_inactive

    @property
    def last_date_str(self) -> str:
        if not self.last_date:
            return "Yozishma yo'q"
        return self.last_date.strftime("%Y-%m-%d")

    def __repr__(self):
        return f"<BotTarget {self.name} ({self.username}) - {self.months_inactive} oy oldin>"

class GroupTarget:
    def __init__(self, dialog, entity, members_count: int, reason: str = "Siz xabar yozmagan guruh"):
        self.dialog = dialog
        self.entity = entity
        self.id = entity.id
        self.name = dialog.name or f"Group_{entity.id}"
        self.username = f"@{entity.username}" if getattr(entity, 'username', None) else "Yopiq guruh"
        self.members_count = members_count
        self.reason = reason

    def __repr__(self):
        return f"<GroupTarget {self.name} ({self.members_count} a'zo)>"

class ChatCleaner:
    def __init__(self, client: TelegramClient, whitelist: Optional[Set] = None):
        self.client = client
        self.whitelist = whitelist or get_whitelist()
        self.delay = get_delete_delay()
        self.revoke = get_revoke_for_all()
        self.block_flood_until = 0.0  # Telegram BlockRequest cheklov vaqti

    async def scan_dialogs(
        self,
        mode: CleanupMode = CleanupMode.EMPTY_AND_JOINED,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> List[ChatTarget]:
        """
        Tezkor skanerlash: dialog.message orqali yozishmasi bor (3+ xabar) chatlarni darhol SKIP qiladi.
        """
        targets: List[ChatTarget] = []
        dialogs = await self.client.get_dialogs()
        total_dialogs = len(dialogs)
        
        for index, dialog in enumerate(dialogs):
            if progress_callback and (index % 10 == 0 or index == total_dialogs - 1):
                progress_callback(index + 1, total_dialogs, dialog.name or "Noma'lum")

            if not dialog.is_user:
                continue

            entity = dialog.entity
            if not entity:
                continue

            if getattr(entity, 'is_self', False):
                continue

            if getattr(entity, 'bot', False):
                continue

            if entity.id in self.whitelist:
                continue
            if entity.username and entity.username.lower() in self.whitelist:
                continue
            if entity.username and f"@{entity.username.lower()}" in self.whitelist:
                continue

            top_msg = dialog.message

            # 1. Butunlay bo'sh chat (0 ta xabar)
            if top_msg is None:
                if mode in (CleanupMode.EMPTY_AND_JOINED, CleanupMode.ALL_SINGLE_MESSAGE):
                    targets.append(ChatTarget(
                        dialog=dialog,
                        entity=entity,
                        reason="Bo'sh chat (0 ta xabar)",
                        message_count=0
                    ))
                continue

            action = getattr(top_msg, 'action', None)
            is_contact_signup = isinstance(action, types.MessageActionContactSignUp)
            top_msg_id = getattr(top_msg, 'id', 1)

            # 2. Faqat "Telegramga qo'shildi" xabari bo'lsa
            if is_contact_signup:
                targets.append(ChatTarget(
                    dialog=dialog,
                    entity=entity,
                    reason="📌 'Telegramga qo'shildi' bildirishnomasi",
                    message_count=1,
                    last_message_text="[Kontakt Telegramga qo'shildi]"
                ))
                continue

            if mode == CleanupMode.JOINED_ONLY:
                continue

            # 3. Yozishma ko'p bo'lsa (ID > 2) -> Darhol SKIP
            if top_msg_id > 2:
                continue

            # 4. Agar ID <= 2 bo'lsa:
            try:
                messages = await self.client.get_messages(dialog.input_entity, limit=3)
            except Exception as e:
                logger.warning(f"Chat xabarlarini olishda xatolik ({dialog.name}): {e}")
                continue

            msg_count = len(messages)

            if msg_count == 0:
                targets.append(ChatTarget(
                    dialog=dialog,
                    entity=entity,
                    reason="Bo'sh chat (0 ta xabar)",
                    message_count=0
                ))
                continue

            if msg_count == 1 and isinstance(getattr(messages[0], 'action', None), types.MessageActionContactSignUp):
                targets.append(ChatTarget(
                    dialog=dialog,
                    entity=entity,
                    reason="📌 'Telegramga qo'shildi' bildirishnomasi",
                    message_count=1,
                    last_message_text="[Kontakt Telegramga qo'shildi]"
                ))
                continue

            if mode == CleanupMode.ALL_SINGLE_MESSAGE and msg_count == 1:
                txt = messages[0].text or ""
                snippet = (txt[:30] + '...') if len(txt) > 30 else txt
                targets.append(ChatTarget(
                    dialog=dialog,
                    entity=entity,
                    reason="1 ta xabarlik nofaol chat",
                    message_count=1,
                    last_message_text=snippet or "[Media/Boshqa]"
                ))

        if progress_callback:
            progress_callback(total_dialogs, total_dialogs, "Tayyor")

        return targets

    async def scan_inactive_bots(
        self,
        months_threshold: float = 9.0,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> List[BotTarget]:
        """
        Tezkor botlarni skanerlash: dialog.date xotirada borligi uchun bir necha soniyada tugaydi.
        """
        targets: List[BotTarget] = []
        dialogs = await self.client.get_dialogs()
        total_dialogs = len(dialogs)
        
        now = datetime.now(timezone.utc)

        for index, dialog in enumerate(dialogs):
            if progress_callback and (index % 10 == 0 or index == total_dialogs - 1):
                progress_callback(index + 1, total_dialogs, dialog.name or "Noma'lum")

            if not dialog.is_user:
                continue

            entity = dialog.entity
            if not entity or not getattr(entity, 'bot', False):
                continue

            if entity.id in self.whitelist:
                continue
            if entity.username and entity.username.lower() in self.whitelist:
                continue
            if entity.username and f"@{entity.username.lower()}" in self.whitelist:
                continue

            last_date = dialog.date

            if last_date:
                if last_date.tzinfo is None:
                    last_date = last_date.replace(tzinfo=timezone.utc)
                diff_days = (now - last_date).total_seconds() / 86400.0
                diff_months = diff_days / 30.4375
            else:
                diff_days = 9999.0
                diff_months = 999.0

            if diff_months >= months_threshold:
                targets.append(BotTarget(
                    dialog=dialog,
                    entity=entity,
                    last_date=last_date,
                    days_inactive=int(diff_days),
                    months_inactive=round(diff_months, 1)
                ))

        targets.sort(key=lambda x: x.days_inactive, reverse=True)

        if progress_callback:
            progress_callback(total_dialogs, total_dialogs, "Tayyor")

        return targets

    async def scan_suspicious_groups(
        self,
        min_members: int = 200,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> List[GroupTarget]:
        """
        Siz umuman xabar yozmagan, majburiy qo'shilgan guruhlarni (200+ a'zoli) aniqlaydi.
        Siz admin yoki creator bo'lgan guruhlar tegilmaydi.
        """
        targets: List[GroupTarget] = []
        dialogs = await self.client.get_dialogs()
        total_dialogs = len(dialogs)

        for index, dialog in enumerate(dialogs):
            if progress_callback and (index % 5 == 0 or index == total_dialogs - 1):
                progress_callback(index + 1, total_dialogs, dialog.name or "Noma'lum")

            if not dialog.is_group:
                continue

            entity = dialog.entity
            if not entity:
                continue

            # O'zingiz yaratgan (Creator) yoki Admin bo'lgan guruhlarni o'tkazib yuborish
            if getattr(entity, 'creator', False):
                continue
            if getattr(entity, 'admin_rights', None) is not None:
                continue

            # Oq ro'yxat tekshiruvi
            if entity.id in self.whitelist:
                continue
            if getattr(entity, 'username', None) and entity.username.lower() in self.whitelist:
                continue
            if getattr(entity, 'username', None) and f"@{entity.username.lower()}" in self.whitelist:
                continue

            # A'zolar sonini aniqlash
            members_count = getattr(entity, 'participants_count', 0) or 0
            if members_count < min_members and members_count != 0:
                continue

            # O'zingiz bu guruhda xabar yozganmisiz tekshirish
            try:
                my_msgs = await self.client.get_messages(dialog.input_entity, from_user='me', limit=1)
                if len(my_msgs) > 0:
                    # Siz xabar yozgansiz, demak kerakli guruh
                    continue
            except Exception as e:
                logger.warning(f"Guruh xabarlarini tekshirishda xatolik ({dialog.name}): {e}")
                continue

            targets.append(GroupTarget(
                dialog=dialog,
                entity=entity,
                members_count=members_count,
                reason=f"Yozilmagan guruh ({members_count}+ a'zo)"
            ))

        targets.sort(key=lambda x: x.members_count, reverse=True)

        if progress_callback:
            progress_callback(total_dialogs, total_dialogs, "Tayyor")

        return targets

    async def delete_target(self, target: ChatTarget) -> Tuple_Result:
        """
        Bitta chatni xavfsiz o'chiradi va FloodWait xatoliklarini avtomatik kutib turadi.
        """
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                await self.client.delete_dialog(target.entity, revoke=self.revoke)
                await asyncio.sleep(self.delay)
                return True, "Muvaffaqiyatli o'chirildi"
            except FloodWaitError as e:
                logger.warning(f"Telegram FloodWait: {e.seconds} soniya kutilmoqda...")
                await asyncio.sleep(e.seconds + 2)
                retry_count += 1
            except RPCError as e:
                logger.error(f"Telegram RPC xatoligi ({target.name}): {e}")
                return False, f"RPC xatosi: {str(e)}"
            except Exception as e:
                logger.error(f"Kutilmagan xatolik ({target.name}): {e}")
                return False, str(e)
                
        return False, "FloodWait tufayli qayta urinishlar tugadi"

    async def delete_and_block_bot(self, target: BotTarget) -> Tuple_Result:
        """
        Botni bloklaydi (agar Flood bo'lmasa) va chat tarixini to'liq o'chiradi.
        """
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                if time.time() >= self.block_flood_until:
                    try:
                        await self.client(functions.contacts.BlockRequest(id=target.entity))
                    except FloodWaitError as fe:
                        self.block_flood_until = time.time() + fe.seconds
                    except Exception:
                        pass

                await self.client.delete_dialog(target.entity, revoke=True)
                await asyncio.sleep(self.delay)
                return True, "O'chirildi"
            except FloodWaitError as e:
                logger.warning(f"Telegram FloodWait: {e.seconds} soniya kutilmoqda...")
                await asyncio.sleep(e.seconds + 2)
                retry_count += 1
            except RPCError as e:
                logger.error(f"Telegram RPC xatoligi ({target.name}): {e}")
                return False, f"RPC xatosi: {str(e)}"
            except Exception as e:
                logger.error(f"Kutilmagan xatolik ({target.name}): {e}")
                return False, str(e)
                
        return False, "FloodWait tufayli qayta urinishlar tugadi"

    async def leave_and_delete_group(self, target: GroupTarget) -> Tuple_Result:
        """
        Guruhdan chiqadi va dialoglar ro'yxatidan o'chiradi.
        """
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                await self.client.delete_dialog(target.entity)
                await asyncio.sleep(self.delay)
                return True, "Guruhdan chiqildi va o'chirildi"
            except FloodWaitError as e:
                logger.warning(f"Telegram FloodWait: {e.seconds} soniya kutilmoqda...")
                await asyncio.sleep(e.seconds + 2)
                retry_count += 1
            except RPCError as e:
                logger.error(f"Telegram RPC xatoligi ({target.name}): {e}")
                return False, f"RPC xatosi: {str(e)}"
            except Exception as e:
                logger.error(f"Kutilmagan xatolik ({target.name}): {e}")
                return False, str(e)
                
        return False, "FloodWait tufayli qayta urinishlar tugadi"

    async def clean_all(
        self,
        targets: List[ChatTarget],
        status_callback: Optional[Callable[[int, int, ChatTarget, bool, str], None]] = None
    ) -> Dict[str, int]:
        stats = {"total": len(targets), "deleted": 0, "failed": 0}
        for index, target in enumerate(targets):
            success, msg = await self.delete_target(target)
            if success:
                stats["deleted"] += 1
            else:
                stats["failed"] += 1
            if status_callback:
                status_callback(index + 1, len(targets), target, success, msg)
        return stats

    async def clean_all_bots(
        self,
        targets: List[BotTarget],
        status_callback: Optional[Callable[[int, int, BotTarget, bool, str], None]] = None
    ) -> Dict[str, int]:
        stats = {"total": len(targets), "deleted": 0, "failed": 0}
        for index, target in enumerate(targets):
            success, msg = await self.delete_and_block_bot(target)
            if success:
                stats["deleted"] += 1
            else:
                stats["failed"] += 1
            if status_callback:
                status_callback(index + 1, len(targets), target, success, msg)
        return stats

    async def clean_all_groups(
        self,
        targets: List[GroupTarget],
        status_callback: Optional[Callable[[int, int, GroupTarget, bool, str], None]] = None
    ) -> Dict[str, int]:
        stats = {"total": len(targets), "deleted": 0, "failed": 0}
        for index, target in enumerate(targets):
            success, msg = await self.leave_and_delete_group(target)
            if success:
                stats["deleted"] += 1
            else:
                stats["failed"] += 1
            if status_callback:
                status_callback(index + 1, len(targets), target, success, msg)
        return stats
