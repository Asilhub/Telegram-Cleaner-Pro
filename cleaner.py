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
        self.username = f"@{entity.username}" if getattr(entity, 'username', None) else "Yopiq / Havolasiz"
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
        self.block_flood_until = 0.0

    @staticmethod
    def get_dialog_stats(dialogs) -> Dict[str, int]:
        stats = {
            "total": len(dialogs),
            "users": 0,
            "bots": 0,
            "groups": 0,
            "channels": 0
        }
        for d in dialogs:
            entity = d.entity
            if d.is_user:
                if getattr(entity, 'bot', False):
                    stats["bots"] += 1
                else:
                    stats["users"] += 1
            elif d.is_group:
                stats["groups"] += 1
            elif d.is_channel:
                stats["channels"] += 1
        return stats

    @staticmethod
    def is_deleted_bot(dialog, entity) -> bool:
        """O'chib ketgan account aslida BOT ekanligini xabarlar strukturasi va tugmalari orqali aniqlaydi"""
        if not getattr(entity, 'deleted', False):
            return False

        if getattr(entity, 'bot', False):
            return True

        if getattr(entity, 'username', None) and entity.username.lower().endswith('bot'):
            return True

        if 'bot' in (dialog.name or '').lower():
            return True

        msg = dialog.message
        if msg:
            if getattr(msg, 'reply_markup', None) is not None:
                return True

            txt = getattr(msg, 'text', '') or ''
            if '/start' in txt.lower() or txt.startswith('/'):
                return True

        return False

    async def get_all_dialogs_summary(self) -> Tuple[Dict[str, int], List[Dict]]:
        """Akauntdagi barcha chatlar va ularning batafsil statistikasi ile ro'yxatini oladi"""
        dialogs = await self.client.get_dialogs()
        stats = self.get_dialog_stats(dialogs)
        dialog_list = []
        for d in dialogs:
            entity = d.entity
            if d.is_user:
                if getattr(entity, 'bot', False):
                    d_type = "🤖 Bot"
                else:
                    d_type = "👤 Shaxsiy"
            elif d.is_group:
                d_type = "👥 Guruh"
            elif d.is_channel:
                d_type = "📢 Kanal"
            else:
                d_type = "💬 Chat"

            name = d.name or f"Chat_{d.id}"
            username = f"@{entity.username}" if getattr(entity, 'username', None) else "-"
            top_msg = d.message
            msg_snippet = ""
            if top_msg:
                txt = top_msg.text or ""
                msg_snippet = (txt[:30] + '...') if len(txt) > 30 else txt

            dialog_list.append({
                "id": d.id,
                "name": name,
                "type": d_type,
                "username": username,
                "date": d.date.strftime("%Y-%m-%d %H:%M") if d.date else "-",
                "unread": d.unread_count,
                "last_msg": msg_snippet
            })

        return stats, dialog_list

    async def categorize_all_dialogs(self) -> Dict[str, List[Dict]]:
        """Akauntdagi barcha chatlarni papkalar va alohida kategoriyalar bo'yicha ajratadi"""
        dialogs = await self.client.get_dialogs()
        
        categories: Dict[str, List[Dict]] = {
            "admin_channels": [],    # 👑 Siz Admin/Ega bo'lgan Kanallar
            "admin_groups": [],      # 👑 Siz Admin/Ega bo'lgan Guruhlar
            "personal_users": [],    # 👤 Shaxsiy Chatlar (Jonli)
            "deleted_users": [],     # 👻 O'chirilgan Hisoblar (Deleted Account)
            "active_bots": [],       # 🤖 Faol Botlar
            "deleted_bots": [],      # 🤖👻 O'chirilgan Botlar (Deleted Bot)
            "public_channels": [],   # 📢 Ommaviy (Public) Kanallar
            "private_channels": [],  # 🔒 Yopiq (Private) Kanallar
            "public_groups": [],     # 👥 Ommaviy (Public) Guruhlar
            "private_groups": []     # 🔒 Yopiq (Private) Guruhlar
        }

        for d in dialogs:
            entity = d.entity
            name = d.name or f"Chat_{d.id}"
            username = f"@{entity.username}" if getattr(entity, 'username', None) else "-"
            top_msg = d.message
            msg_snippet = ""
            if top_msg:
                txt = top_msg.text or ""
                msg_snippet = (txt[:30] + '...') if len(txt) > 30 else txt

            item = {
                "id": d.id,
                "name": name,
                "username": username,
                "date": d.date.strftime("%Y-%m-%d %H:%M") if d.date else "-",
                "unread": d.unread_count,
                "last_msg": msg_snippet
            }

            if d.is_user:
                is_deleted = getattr(entity, 'deleted', False)
                is_bot = getattr(entity, 'bot', False)
                is_del_bot = self.is_deleted_bot(d, entity)

                if is_deleted and is_del_bot:
                    categories["deleted_bots"].append(item)
                elif is_deleted:
                    categories["deleted_users"].append(item)
                elif is_bot:
                    categories["active_bots"].append(item)
                else:
                    categories["personal_users"].append(item)

            elif d.is_channel and not d.is_group:
                # Broadcast Channel
                is_admin = getattr(entity, 'creator', False) or getattr(entity, 'admin_rights', None) is not None
                if is_admin:
                    categories["admin_channels"].append(item)
                elif getattr(entity, 'username', None):
                    categories["public_channels"].append(item)
                else:
                    categories["private_channels"].append(item)

            elif d.is_group:
                # Basic Group or Supergroup (Megagroup)
                is_admin = getattr(entity, 'creator', False) or getattr(entity, 'admin_rights', None) is not None
                if is_admin:
                    categories["admin_groups"].append(item)
                elif getattr(entity, 'username', None):
                    categories["public_groups"].append(item)
                else:
                    categories["private_groups"].append(item)

        return categories

    async def create_telegram_folders(self) -> Dict[str, str]:
        """
        Telegram ilovasining o'zida avtomatik ravishda haqiqiy Chat Papkalarini (Folders) yaratadi.
        """
        results = {}
        dialogs = await self.client.get_dialogs()

        admin_peers = []
        deleted_user_peers = []
        deleted_bot_peers = []

        for d in dialogs:
            entity = d.entity
            try:
                input_p = utils.get_input_peer(entity)
            except Exception:
                input_p = d.input_entity

            if not input_p:
                continue

            if d.is_user and getattr(entity, 'deleted', False):
                if self.is_deleted_bot(d, entity):
                    deleted_bot_peers.append(input_p)
                else:
                    deleted_user_peers.append(input_p)
            elif d.is_channel or d.is_group:
                is_admin = getattr(entity, 'creator', False) or getattr(entity, 'admin_rights', None) is not None
                if is_admin:
                    admin_peers.append(input_p)

        all_deleted_peers = deleted_user_peers + deleted_bot_peers

        existing_title_to_id = {}
        used_ids = []
        try:
            existing_filters = await self.client(functions.messages.GetDialogFiltersRequest())
            for f in existing_filters:
                if hasattr(f, 'id'):
                    if f.id not in used_ids:
                        used_ids.append(f.id)
                    t_str = ""
                    if hasattr(f, 'title'):
                        if isinstance(f.title, types.TextWithEntities):
                            t_str = f.title.text
                        elif isinstance(f.title, str):
                            t_str = f.title
                    if t_str:
                        existing_title_to_id[t_str.strip().lower()] = f.id
        except Exception:
            used_ids = []

        def get_id_for_title(clean_title: str) -> int:
            clean_lower = clean_title.lower()
            for k, fid in existing_title_to_id.items():
                if clean_lower in k or k in clean_lower:
                    return fid
            for i in range(2, 30):
                if i not in used_ids:
                    used_ids.append(i)
                    return i
            return 2

        folder_definitions = [
            ("Admin", "👑", {"include_peers": admin_peers[:100]}, len(admin_peers) > 0),
            ("Shaxsiy", "👤", {"contacts": True, "non_contacts": True, "bots": False, "groups": False, "broadcasts": False}, True),
            ("Botlar", "🤖", {"bots": True, "contacts": False, "non_contacts": False, "groups": False, "broadcasts": False}, True),
            ("Kanallar", "📢", {"broadcasts": True, "contacts": False, "non_contacts": False, "groups": False, "bots": False}, True),
            ("Guruhlar", "👥", {"groups": True, "contacts": False, "non_contacts": False, "broadcasts": False, "bots": False}, True),
            ("Deleted", "👻", {"include_peers": all_deleted_peers[:100]}, len(all_deleted_peers) > 0),
            ("Deleted Bot", "🤖", {"include_peers": deleted_bot_peers[:100]}, True),
        ]

        active_order_ids = []

        for title, emoji, kwargs, condition in folder_definitions:
            if not condition:
                continue
            folder_id = get_id_for_title(title)
            if folder_id not in active_order_ids:
                active_order_ids.append(folder_id)

            df = types.DialogFilter(
                id=folder_id,
                title=types.TextWithEntities(text=title, entities=[]),
                emoticon=emoji,
                pinned_peers=[],
                include_peers=kwargs.get("include_peers", []),
                exclude_peers=[],
                contacts=kwargs.get("contacts", None),
                non_contacts=kwargs.get("non_contacts", None),
                groups=kwargs.get("groups", None),
                broadcasts=kwargs.get("broadcasts", None),
                bots=kwargs.get("bots", None)
            )
            try:
                await self.client(functions.messages.UpdateDialogFilterRequest(id=folder_id, filter=df))
                results[title] = "Muvaffaqiyatli yangilandi ✓"
            except Exception as e:
                results[title] = f"Xatolik: {e}"

        # Update folder ordering so Telegram Desktop refreshes instantly
        if active_order_ids:
            try:
                all_ids = list(dict.fromkeys(active_order_ids + used_ids))
                await self.client(functions.messages.UpdateDialogFiltersOrderRequest(order=all_ids))
            except Exception:
                pass

        return results

    async def scan_dialogs(
        self,
        mode: CleanupMode = CleanupMode.EMPTY_AND_JOINED,
        include_my_single: bool = False,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> Tuple[List[ChatTarget], Dict[str, int]]:
        """
        Tezkor skanerlash: dialog.message orqali yozishmasi bor (3+ xabar) chatlarni darhol SKIP qiladi.
        include_my_single: Foydalanuvchi o'zi 1 ta xabar yozgan (javobsiz qolgan) chatlar ham qo'shilsinmi.
        """
        targets: List[ChatTarget] = []
        dialogs = await self.client.get_dialogs()
        stats = self.get_dialog_stats(dialogs)
        total_dialogs = stats["total"]
        
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
                        reason="📭 Bo'sh chat (0 ta xabar)",
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
                    reason="📭 Bo'sh chat (0 ta xabar)",
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

            # Faqat 1 ta xabar bo'lgan holat
            if mode == CleanupMode.ALL_SINGLE_MESSAGE and msg_count == 1:
                first_msg = messages[0]
                is_out = getattr(first_msg, 'out', False)
                txt = first_msg.text or ""
                snippet = (txt[:30] + '...') if len(txt) > 30 else txt

                if is_out:
                    # O'zingiz yozgan xabar
                    if include_my_single:
                        targets.append(ChatTarget(
                            dialog=dialog,
                            entity=entity,
                            reason="📤 O'zingiz yozgan javobsiz chat (1 ta xabar)",
                            message_count=1,
                            last_message_text=f"Siz: {snippet or '[Media/Stiker]'}"
                        ))
                    else:
                        # O'zingiz yozgan chatlarni saqlab qolish
                        continue
                else:
                    # Narigi tomon yozgan 1 ta xabar
                    targets.append(ChatTarget(
                        dialog=dialog,
                        entity=entity,
                        reason="✉️ Narigi tomon yozgan nofaol chat (1 ta xabar)",
                        message_count=1,
                        last_message_text=f"U: {snippet or '[Media/Stiker]'}"
                    ))

        if progress_callback:
            progress_callback(total_dialogs, total_dialogs, "Tayyor")

        return targets, stats

    async def scan_inactive_bots(
        self,
        months_threshold: float = 9.0,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> Tuple[List[BotTarget], Dict[str, int]]:
        targets: List[BotTarget] = []
        dialogs = await self.client.get_dialogs()
        stats = self.get_dialog_stats(dialogs)
        total_dialogs = stats["total"]
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

        return targets, stats

    async def scan_suspicious_groups(
        self,
        min_members: int = 200,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> Tuple[List[GroupTarget], Dict[str, int]]:
        targets: List[GroupTarget] = []
        dialogs = await self.client.get_dialogs()
        stats = self.get_dialog_stats(dialogs)
        total_dialogs = stats["total"]

        me = await self.client.get_me()
        my_id = me.id

        for index, dialog in enumerate(dialogs):
            if progress_callback and (index % 5 == 0 or index == total_dialogs - 1):
                progress_callback(index + 1, total_dialogs, dialog.name or "Noma'lum")

            if not dialog.is_group:
                continue

            entity = dialog.entity
            if not entity:
                continue

            if isinstance(entity, types.Chat):
                continue

            if getattr(entity, 'creator', False):
                continue
            if getattr(entity, 'admin_rights', None) is not None:
                continue

            if entity.id in self.whitelist:
                continue
            if getattr(entity, 'username', None) and entity.username.lower() in self.whitelist:
                continue
            if getattr(entity, 'username', None) and f"@{entity.username.lower()}" in self.whitelist:
                continue

            members_count = getattr(entity, 'participants_count', None)
            if members_count is None:
                try:
                    full = await self.client(functions.channels.GetFullChannelRequest(channel=dialog.input_entity))
                    members_count = full.full_chat.participants_count or 0
                except Exception:
                    members_count = 0

            if members_count < min_members:
                continue

            user_participated = False
            try:
                recent_msgs = await self.client.get_messages(dialog.input_entity, limit=40)
                for m in recent_msgs:
                    if getattr(m, 'out', False) or getattr(m, 'sender_id', None) == my_id or getattr(m, 'from_id', None) == my_id:
                        user_participated = True
                        break

                if not user_participated:
                    my_msgs = await self.client.get_messages(dialog.input_entity, from_user='me', limit=1)
                    if len(my_msgs) > 0:
                        user_participated = True

                if not user_participated:
                    my_id_msgs = await self.client.get_messages(dialog.input_entity, from_user=my_id, limit=1)
                    if len(my_id_msgs) > 0:
                        user_participated = True

            except Exception as e:
                logger.warning(f"Guruh xabarlarini tekshirishda ogohlantirish ({dialog.name}): {e}")
                continue

            if user_participated:
                continue

            targets.append(GroupTarget(
                dialog=dialog,
                entity=entity,
                members_count=members_count,
                reason=f"Yozilmagan katta guruh ({members_count:,} a'zo)"
            ))

        targets.sort(key=lambda x: x.members_count, reverse=True)

        if progress_callback:
            progress_callback(total_dialogs, total_dialogs, "Tayyor")

        return targets, stats

    async def delete_target(self, target: ChatTarget) -> Tuple_Result:
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
