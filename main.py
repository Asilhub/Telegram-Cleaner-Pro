import os
import sys
import asyncio
from pathlib import Path
from typing import List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich import print as rprint

from config import (
    get_api_credentials,
    save_api_credentials,
    get_delete_delay,
    get_revoke_for_all,
    get_whitelist,
    SESSIONS_DIR,
    ENV_PATH
)
from session_manager import SessionManager
from cleaner import ChatCleaner, CleanupMode, ChatTarget, BotTarget, GroupTarget
from telethon.errors import (
    SessionPasswordNeededError,
    PhoneCodeInvalidError,
    PhoneNumberInvalidError,
    PasswordHashInvalidError
)

console = Console()
session_mgr = SessionManager()

def print_banner():
    banner_text = """[bold cyan]╔══════════════════════════════════════════════════════════════════════════════╗[/bold cyan]
[bold cyan]║[/bold cyan]  [bold yellow]🧹 TELEGRAM CLEANER PRO — HISOB VA GURUHLARNI TOZALOVCHI USERBOT[/bold yellow]           [bold cyan]║[/bold cyan]
[bold cyan]║[/bold cyan]  [dim]Bo'sh chatlar, keraksiz botlar va shubhali guruhlarni avtomatik tozalash[/dim]      [bold cyan]║[/bold cyan]
[bold cyan]╚══════════════════════════════════════════════════════════════════════════════╝[/bold cyan]"""
    console.print(banner_text)

def check_or_prompt_api_credentials():
    api_id, api_hash = get_api_credentials()
    return api_id, api_hash

async def add_new_account(api_id: int, api_hash: str):
    console.print(Panel("[bold cyan]➕ Yangi Telegram hisob qo'shish[/bold cyan]", border_style="cyan"))
    
    session_name = Prompt.ask(
        "[bold yellow]Hisob uchun nom bering[/bold yellow] (masalan: [italic]asosiy, ish_akaunt, profil1[/italic])"
    ).strip()
    
    if not session_name:
        console.print("[red]Nom bo'sh bo'lishi mumkin emas![/red]")
        return

    session_name = "".join(c for c in session_name if c.isalnum() or c in ("_", "-"))
    client = session_mgr.get_client(session_name, api_id, api_hash)

    try:
        await client.connect()
        if await client.is_user_authorized():
            info = await session_mgr.get_account_info(client)
            console.print(f"[bold green]✓ Ushbu hisob allaqachon ulangan:[/bold green] {info['first_name']} ({info['phone']})")
            await client.disconnect()
            return

        phone = Prompt.ask("[bold green]Telefon raqamingizni kiriting[/bold green] (masalan: [cyan]+998901234567[/cyan])").strip()
        
        with console.status("[yellow]Tasdiqlash kodi yuborilmoqda...[/yellow]"):
            send_code_result = await client.send_code_request(phone)

        code = Prompt.ask("[bold green]Telegramga kelgan tasdiqlash kodini kiriting[/bold green]").strip()
        
        try:
            await client.sign_in(phone, code, phone_code_hash=send_code_result.phone_code_hash)
        except SessionPasswordNeededError:
            console.print("[yellow]🔒 Ushbu hisobda Ikki bosqichli autentifikatsiya (2FA Parol) yoqilgan.[/yellow]")
            password = Prompt.ask("[bold green]2FA parolingizni kiriting[/bold green]", password=True)
            await client.sign_in(password=password)

        me = await client.get_me()
        console.print(Panel(
            f"[bold green]✓ Hisob muvaffaqiyatli ulandi![/bold green]\n\n"
            f"👤 Ism: [bold]{me.first_name} {me.last_name or ''}[/bold]\n"
            f"📱 Telefon: [cyan]+{me.phone}[/cyan]\n"
            f"🆔 ID: [dim]{me.id}[/dim]\n"
            f"📁 Sessiya nomi: [yellow]{session_name}.session[/yellow]",
            title="Muvaffaqiyatli",
            border_style="green"
        ))

    except PhoneNumberInvalidError:
        console.print("[bold red]❌ Telefon raqam noto'g'ri kiritildi![/bold red]")
    except PhoneCodeInvalidError:
        console.print("[bold red]❌ Tasdiqlash kodi noto'g'ri![/bold red]")
    except PasswordHashInvalidError:
        console.print("[bold red]❌ 2FA parol noto'g'ri![/bold red]")
    except Exception as e:
        console.print(f"[bold red]❌ Xatolik yuz berdi: {e}[/bold red]")
    finally:
        if client.is_connected():
            await client.disconnect()

async def list_accounts(api_id: int, api_hash: str):
    console.print(Panel("[bold cyan]📱 Ulangan Telegram hisoblari[/bold cyan]", border_style="cyan"))
    
    with console.status("[yellow]Hisoblar yuklanmoqda...[/yellow]"):
        accounts = await session_mgr.load_all_accounts_info(api_id, api_hash)

    if not accounts:
        console.print("[yellow]Hozircha hech qanday hisob ulanmagan. Yangi hisob qo'shish uchun menyudan 5-bandni tanlang.[/yellow]\n")
        return []

    table = Table(title="Sessiyalar Ro'yxati", show_lines=True)
    table.add_column("№", style="dim", justify="center")
    table.add_column("Sessiya nomi", style="bold yellow")
    table.add_column("Ism", style="white")
    table.add_column("Username", style="cyan")
    table.add_column("Telefon", style="green")
    table.add_column("Holat", style="bold")

    for i, acc in enumerate(accounts, 1):
        if "error" in acc and not acc.get("first_name"):
            table.add_row(
                str(i),
                acc["session_name"],
                "-",
                "-",
                "-",
                f"[red]{acc['error']}[/red]"
            )
        else:
            table.add_row(
                str(i),
                acc["session_name"],
                f"{acc['first_name']} {acc['last_name']}".strip(),
                acc["username"],
                acc["phone"],
                "[green]Faol ✓[/green]"
            )

    console.print(table)
    return accounts

def select_mode() -> tuple[CleanupMode, bool]:
    console.print("\n[bold]Qaysi tozalash rejimini tanlaysiz?[/bold]")
    console.print("  [bold cyan]1.[/bold cyan] Faqat 'Telegramga qo'shildi' servis xabarlari bor chatlar")
    console.print("  [bold cyan]2.[/bold cyan] Bo'sh chatlar (0 ta xabar) + 'Telegramga qo'shildi' chatlari ([italic green]Tavsiya etiladi[/italic green])")
    console.print("  [bold cyan]3.[/bold cyan] Faqat 1 ta xabardan iborat bo'lgan barcha nofaol chatlar")
    
    choice = Prompt.ask("Rejimni tanlang", choices=["1", "2", "3"], default="2")
    if choice == "1":
        return CleanupMode.JOINED_ONLY, False
    elif choice == "3":
        include_my_single = Confirm.ask(
            "\n[bold yellow]O'zingiz 1 ta xabar yozgan (lekin javobsiz qolgan) chatlar ham qo'shilsinmi?[/bold yellow]",
            default=False
        )
        return CleanupMode.ALL_SINGLE_MESSAGE, include_my_single
    return CleanupMode.EMPTY_AND_JOINED, False

async def process_account_cleaning(client, session_name: str, dry_run: bool, mode: CleanupMode, include_my_single: bool = False):
    cleaner = ChatCleaner(client)
    console.print(f"\n[bold yellow]🔍 [{session_name}] Shaxsiy chatlar skanerlanmoqda...[/bold yellow]")
    
    targets: List[ChatTarget] = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Skanerlash...", total=100)
        
        def progress_cb(current, total, name):
            progress.update(task, total=total, completed=current, description=f"[cyan]Skanerlanmoqda: [white]{name[:20]}[/white]")

        await client.connect()
        targets, stats = await cleaner.scan_dialogs(mode=mode, include_my_single=include_my_single, progress_callback=progress_cb)

    console.print(Panel(
        f"📊 [bold yellow]Akauntdagi jami chatlar:[/bold yellow] [bold white]{stats['total']}[/bold white] ta\n"
        f"└─ 👤 Shaxsiy: [cyan]{stats['users']}[/cyan] | 🤖 Botlar: [cyan]{stats['bots']}[/cyan] | 👥 Guruhlar: [cyan]{stats['groups']}[/cyan] | 📢 Kanallar: [cyan]{stats['channels']}[/cyan]\n"
        f"🎯 [bold red]Tozalash uchun saralangan chatlar:[/bold red] [bold white]{len(targets)}[/bold white] ta",
        title=f"[{session_name}] Account Statistikasi",
        border_style="cyan"
    ))

    if not targets:
        console.print(f"[bold green]✓ [{session_name}] Tozalash uchun keraksiz/bo'sh chatlar topilmadi![/bold green]")
        return

    table = Table(title=f"[{session_name}] O'chiriladigan Chatlar ({len(targets)} ta)", show_lines=True)
    table.add_column("№", justify="center", style="dim")
    table.add_column("Foydalanuvchi", style="bold")
    table.add_column("Username / Tel", style="cyan")
    table.add_column("Sabab", style="yellow")
    table.add_column("Xabarlar", justify="center")

    for i, t in enumerate(targets, 1):
        info_str = t.username if t.username else (t.phone if t.phone else f"ID: {t.id}")
        table.add_row(str(i), t.name, info_str, t.reason, str(t.message_count))

    console.print(table)

    if dry_run:
        console.print(f"[dim]ℹ️ Sinov (Dry Run) rejimi: Hech qanday chat o'chirilmadi.[/dim]")
        return

    confirm = Confirm.ask(
        f"[bold red]⚠️ Yuqoridagi {len(targets)} ta chat butunlay o'chirilsinmi?[/bold red]",
        default=False
    )
    if not confirm:
        console.print("[yellow]Amal bekor qilindi.[/yellow]")
        return

    console.print(f"\n[bold red]🧹 Chatlar o'chirilmoqda (Kechikish: {cleaner.delay}s)...[/bold red]")
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        task = progress.add_task("[red]O'chirilmoqda...", total=len(targets))

        def status_cb(current, total, target, success, msg):
            status_text = "[green]O'chirildi[/green]" if success else f"[red]{msg}[/red]"
            progress.update(task, completed=current, description=f"[bold]{target.name[:15]}[/bold]: {status_text}")

        stats = await cleaner.clean_all(targets, status_callback=status_cb)

    console.print(Panel(
        f"[bold green]✓ Tozalash yakunlandi![/bold green]\n\n"
        f"📊 Jami topilgan: [bold]{stats['total']}[/bold]\n"
        f"🗑️ O'chirildi: [bold green]{stats['deleted']}[/bold green]\n"
        f"❌ Xatoliklar: [bold red]{stats['failed']}[/bold red]",
        title=f"[{session_name}] Natija",
        border_style="green"
    ))

async def process_bot_cleaning(client, session_name: str, months_threshold: float, dry_run: bool):
    cleaner = ChatCleaner(client)
    console.print(f"\n[bold yellow]🔍 [{session_name}] Nofaol botlar skanerlanmoqda (Chegara: {months_threshold} oy)...[/bold yellow]")
    
    bot_targets: List[BotTarget] = []
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Botlarni skanerlash...", total=100)
        def progress_cb(current, total, name):
            progress.update(task, total=total, completed=current, description=f"[cyan]Tekshirilmoqda: [white]{name[:20]}[/white]")

        await client.connect()
        bot_targets, stats = await cleaner.scan_inactive_bots(months_threshold=months_threshold, progress_callback=progress_cb)

    console.print(Panel(
        f"📊 [bold yellow]Akauntdagi jami chatlar:[/bold yellow] [bold white]{stats['total']}[/bold white] ta "
        f"([cyan]🤖 Jami botlar: {stats['bots']}[/cyan])\n"
        f"🎯 [bold red]Nofaol ({months_threshold}+ oy) botlar:[/bold red] [bold white]{len(bot_targets)}[/bold white] ta",
        title=f"[{session_name}] Botlar Statistikasi",
        border_style="cyan"
    ))

    if not bot_targets:
        console.print(f"[bold green]✓ [{session_name}] {months_threshold}+ oydan beri ishlatilmagan nofaol botlar topilmadi![/bold green]")
        return

    table = Table(title=f"[{session_name}] {months_threshold}+ Oydan beri nofaol botlar ({len(bot_targets)} ta)", show_lines=True)
    table.add_column("№", justify="center", style="dim")
    table.add_column("Bot nomi", style="bold")
    table.add_column("Username", style="cyan")
    table.add_column("Oxirgi faollik", style="yellow")
    table.add_column("Faolsiz muddat", style="magenta", justify="center")

    for i, b in enumerate(bot_targets, 1):
        table.add_row(str(i), b.name, b.username, b.last_date_str, f"{b.months_inactive} oy oldin ({b.days_inactive} kun)")

    console.print(table)

    if dry_run:
        console.print(f"[dim]ℹ️ Sinov (Dry Run) rejimi: Hech qanday bot bloklanmadi yoki o'chirilmadi.[/dim]")
        return

    confirm = Confirm.ask(
        f"[bold red]⚠️ Yuqoridagi {len(bot_targets)} ta botni BLOKLASH va CHATINI O'CHIRISHNI tasdiqlaysizmi?[/bold red]",
        default=False
    )
    if not confirm:
        console.print("[yellow]Amal bekor qilindi.[/yellow]")
        return

    console.print(f"\n[bold red]🤖 Botlar bloklanmoqda va o'chirilmoqda (Kechikish: {cleaner.delay}s)...[/bold red]")
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        task = progress.add_task("[red]Tozalanmoqda...", total=len(bot_targets))

        def status_cb(current, total, target, success, msg):
            status_text = "[green]Bloklandi & O'chirildi[/green]" if success else f"[red]{msg}[/red]"
            progress.update(task, completed=current, description=f"[bold]{target.name[:15]}[/bold]: {status_text}")

        stats = await cleaner.clean_all_bots(bot_targets, status_callback=status_cb)

    console.print(Panel(
        f"[bold green]✓ Botlarni tozalash yakunlandi![/bold green]\n\n"
        f"📊 Jami topilgan: [bold]{stats['total']}[/bold]\n"
        f"🚫 Bloklandi va o'chirildi: [bold green]{stats['deleted']}[/bold green]\n"
        f"❌ Xatoliklar: [bold red]{stats['failed']}[/bold red]",
        title=f"[{session_name}] Natija",
        border_style="green"
    ))

async def process_group_cleaning(client, session_name: str, min_members: int, dry_run: bool):
    cleaner = ChatCleaner(client)
    console.print(f"\n[bold yellow]🔍 [{session_name}] Shubhali guruhlar skanerlanmoqda (A'zolari: {min_members}+ ta)...[/bold yellow]")

    group_targets: List[GroupTarget] = []
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Guruhlarni tekshirish...", total=100)
        def progress_cb(current, total, name):
            progress.update(task, total=total, completed=current, description=f"[cyan]Tekshirilmoqda: [white]{name[:20]}[/white]")

        await client.connect()
        group_targets, stats = await cleaner.scan_suspicious_groups(min_members=min_members, progress_callback=progress_cb)

    console.print(Panel(
        f"📊 [bold yellow]Akauntdagi jami chatlar:[/bold yellow] [bold white]{stats['total']}[/bold white] ta "
        f"([cyan]👥 Jami guruhlar: {stats['groups']}[/cyan])\n"
        f"🎯 [bold red]Shubhali/Yozilmagan guruhlar ({min_members}+ a'zoli):[/bold red] [bold white]{len(group_targets)}[/bold white] ta",
        title=f"[{session_name}] Guruhlar Statistikasi",
        border_style="cyan"
    ))

    if not group_targets:
        console.print(f"[bold green]✓ [{session_name}] Siz yozmagan {min_members}+ a'zoli shubhali guruhlar topilmadi![/bold green]")
        return

    table = Table(title=f"[{session_name}] Shubhali / Majburiy qo'shilgan guruhlar ({len(group_targets)} ta)", show_lines=True)
    table.add_column("№", justify="center", style="dim")
    table.add_column("Guruh nomi", style="bold")
    table.add_column("Username / Havola", style="cyan")
    table.add_column("A'zolar soni", style="magenta", justify="center")
    table.add_column("Sizning xabarlaringiz", style="green", justify="center")

    for i, g in enumerate(group_targets, 1):
        table.add_row(
            str(i),
            g.name,
            g.username,
            f"{g.members_count:,} ta" if g.members_count else "Noma'lum",
            "0 ta (Yozilmagan)"
        )

    console.print(table)

    if dry_run:
        console.print(f"[dim]ℹ️ Sinov (Dry Run) rejimi: Hech qanday guruhdan chiqilmadi.[/dim]")
        return

    console.print("\n[bold]Chiqmoqchi bo'lgan guruhlaringizni tanlang:[/bold]")
    console.print("  • [bold green]all[/bold green] — Jadvaldagi barcha guruhlardan chiqish")
    console.print("  • [bold yellow]1, 3, 5[/bold yellow] — Faqat tanlangan raqamlardagi guruhlardan chiqish")
    console.print("  • [bold red]0[/bold red] — Bekor qilish")
    
    choice = Prompt.ask("\nTanlovingizni kiriting", default="all").strip().lower()

    if choice in ("0", "cancel", "yoq", "n"):
        console.print("[yellow]Amal bekor qilindi.[/yellow]")
        return

    selected_targets = []
    if choice == "all":
        selected_targets = group_targets
    else:
        try:
            indices = set()
            for part in choice.split(","):
                part = part.strip()
                if "-" in part:
                    start, end = map(int, part.split("-"))
                    indices.update(range(start, end + 1))
                elif part.isdigit():
                    indices.add(int(part))
            
            selected_targets = [group_targets[i - 1] for i in sorted(indices) if 1 <= i <= len(group_targets)]
        except Exception:
            console.print("[red]Noto'g'ri tanlov kiritildi![/red]")
            return

    if not selected_targets:
        console.print("[yellow]Hech qanday guruh tanlanmadi.[/yellow]")
        return

    confirm = Confirm.ask(
        f"[bold red]⚠️ Tanlangan {len(selected_targets)} ta guruhdan CHIQISH va O'CHIRISHNI tasdiqlaysizmi?[/bold red]",
        default=False
    )
    if not confirm:
        console.print("[yellow]Amal bekor qilindi.[/yellow]")
        return

    console.print(f"\n[bold red]👥 Guruhlardan chiqilmoqda (Kechikish: {cleaner.delay}s)...[/bold red]")
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        task = progress.add_task("[red]Guruhlardan chiqilmoqda...", total=len(selected_targets))

        def status_cb(current, total, target, success, msg):
            status_text = "[green]Chiqildi & O'chirildi[/green]" if success else f"[red]{msg}[/red]"
            progress.update(task, completed=current, description=f"[bold]{target.name[:15]}[/bold]: {status_text}")

        stats = await cleaner.clean_all_groups(selected_targets, status_callback=status_cb)

    console.print(Panel(
        f"[bold green]✓ Guruhlarni tozalash yakunlandi![/bold green]\n\n"
        f"📊 Jami topilgan: [bold]{stats['total']}[/bold]\n"
        f"🚪 Chiqildi va o'chirildi: [bold green]{stats['deleted']}[/bold green]\n"
        f"❌ Xatoliklar: [bold red]{stats['failed']}[/bold red]",
        title=f"[{session_name}] Natija",
        border_style="green"
    ))

async def process_deleted_accounts_cleaning(client, session_name: str, dry_run: bool):
    cleaner = ChatCleaner(client)
    console.print(f"\n[bold yellow]🔍 [{session_name}] Faqat TEKST yozishmasi bor 'Deleted Account'lar skanerlanmoqda (Media borlari saqlanadi)...[/bold yellow]")

    targets: List[ChatTarget] = []
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Deleted chatlarni tekshirish...", total=100)
        def progress_cb(current, total, name):
            progress.update(task, total=total, completed=current, description=f"[cyan]Tekshirilmoqda: [white]{name[:20]}[/white]")

        await client.connect()
        targets, stats = await cleaner.scan_deleted_accounts_without_media(progress_callback=progress_cb)

    console.print(Panel(
        f"📊 [bold yellow]Akauntdagi jami chatlar:[/bold yellow] [bold white]{stats['total']}[/bold white] ta\n"
        f"🎯 [bold red]Faqat TEKST xabari bor (O'chiriladigan) Deleted Account'lar:[/bold red] [bold white]{len(targets)}[/bold white] ta\n"
        f"🛡️ [bold green]Rasm / Ovoz / Video borligi tufayli SAQLAB QOLINGAN Deleted Account'lar kiritilmadi![/bold green]",
        title=f"[{session_name}] Deleted Account'lar Statistikasi",
        border_style="cyan"
    ))

    if not targets:
        console.print(f"[bold green]✓ [{session_name}] O'chirish uchun faqat tekstli Deleted Account'lar topilmadi![/bold green]")
        return

    table = Table(title=f"[{session_name}] Faqat Tekstli O'chiriladigan Deleted Account'lar ({len(targets)} ta)", show_lines=True)
    table.add_column("№", justify="center", style="dim")
    table.add_column("Foydalanuvchi", style="bold red")
    table.add_column("Sabab", style="yellow")
    table.add_column("Xabarlar soni", justify="center")

    for i, t in enumerate(targets, 1):
        table.add_row(str(i), t.name, t.reason, str(t.message_count))

    console.print(table)

    if dry_run:
        console.print(f"[dim]ℹ️ Sinov (Dry Run) rejimi: Hech qanday Deleted Account o'chirilmadi.[/dim]")
        return

    confirm = Confirm.ask(
        f"[bold red]⚠️ Yuqoridagi {len(targets)} ta faqat tekstli Deleted Account'larni O'CHIRISHNI tasdiqlaysizmi?[/bold red]",
        default=False
    )
    if not confirm:
        console.print("[yellow]Amal bekor qilindi.[/yellow]")
        return

    console.print(f"\n[bold red]🧹 Deleted Account'lar o'chirilmoqda (Kechikish: {cleaner.delay}s)...[/bold red]")
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        task = progress.add_task("[red]O'chirilmoqda...", total=len(targets))

        def status_cb(current, total, target, success, msg):
            status_text = "[green]O'chirildi[/green]" if success else f"[red]{msg}[/red]"
            progress.update(task, completed=current, description=f"[bold]{target.name[:15]}[/bold]: {status_text}")

        stats_res = await cleaner.clean_all(targets, status_callback=status_cb)

    console.print(Panel(
        f"[bold green]✓ Deleted Account'larni tozalash yakunlandi![/bold green]\n\n"
        f"📊 Jami topilgan: [bold]{stats_res['total']}[/bold]\n"
        f"🗑️ O'chirildi: [bold green]{stats_res['deleted']}[/bold green]\n"
        f"❌ Xatoliklar: [bold red]{stats_res['failed']}[/bold red]",
        title=f"[{session_name}] Natija",
        border_style="green"
    ))

async def run_deleted_accounts_cleaner_flow(api_id: int, api_hash: str, dry_run: bool):
    sessions = session_mgr.list_sessions()
    if not sessions:
        console.print("[yellow]Hech qanday hisob ulanmagan! Avval hisob qo'shing.[/yellow]")
        return

    console.print("\n[bold]Qaysi hisobdagi Deleted Account'larni tozalamoqchisiz?[/bold]")
    console.print("  [bold cyan]0.[/bold cyan] 🌐 Barcha hisoblar bo'yicha")
    for i, s in enumerate(sessions, 1):
        console.print(f"  [bold cyan]{i}.[/bold cyan] 📱 {s.stem}")

    choice = Prompt.ask("Tanlang", choices=[str(i) for i in range(len(sessions) + 1)], default="0")

    if choice == "0":
        for s in sessions:
            client = session_mgr.get_client(s.stem, api_id, api_hash)
            try:
                await client.connect()
                if await client.is_user_authorized():
                    await process_deleted_accounts_cleaning(client, s.stem, dry_run=dry_run)
                else:
                    console.print(f"[red]⚠️ [{s.stem}] Sessiyasi faol emas, o'tkazib yuborildi.[/red]")
            finally:
                if client.is_connected():
                    await client.disconnect()
    else:
        selected_session = sessions[int(choice) - 1]
        client = session_mgr.get_client(selected_session.stem, api_id, api_hash)
        try:
            await client.connect()
            if await client.is_user_authorized():
                await process_deleted_accounts_cleaning(client, selected_session.stem, dry_run=dry_run)
            else:
                console.print(f"[red]⚠️ [{selected_session.stem}] Sessiyasi faol emas.[/red]")
        finally:
            if client.is_connected():
                await client.disconnect()

async def run_cleaner_flow(api_id: int, api_hash: str, dry_run: bool):
    sessions = session_mgr.list_sessions()
    if not sessions:
        console.print("[yellow]Hech qanday hisob ulanmagan! Avval hisob qo'shing (Menyuda 5).[/yellow]")
        return

    console.print("\n[bold]Qaysi hisobni tozalamoqchisiz?[/bold]")
    console.print("  [bold cyan]0.[/bold cyan] 🌐 Barcha hisoblarni ketma-ket tozalash")
    for i, s in enumerate(sessions, 1):
        console.print(f"  [bold cyan]{i}.[/bold cyan] 📱 {s.stem}")

    choice = Prompt.ask("Tanlang", choices=[str(i) for i in range(len(sessions) + 1)], default="0")
    mode, include_my_single = select_mode()

    if choice == "0":
        for s in sessions:
            client = session_mgr.get_client(s.stem, api_id, api_hash)
            try:
                await client.connect()
                if await client.is_user_authorized():
                    await process_account_cleaning(client, s.stem, dry_run=dry_run, mode=mode, include_my_single=include_my_single)
                else:
                    console.print(f"[red]⚠️ [{s.stem}] Sessiyasi faol emas, o'tkazib yuborildi.[/red]")
            finally:
                if client.is_connected():
                    await client.disconnect()
    else:
        selected_session = sessions[int(choice) - 1]
        client = session_mgr.get_client(selected_session.stem, api_id, api_hash)
        try:
            await client.connect()
            if await client.is_user_authorized():
                await process_account_cleaning(client, selected_session.stem, dry_run=dry_run, mode=mode, include_my_single=include_my_single)
            else:
                console.print(f"[red]⚠️ [{selected_session.stem}] Sessiyasi faol emas.[/red]")
        finally:
            if client.is_connected():
                await client.disconnect()

async def run_bot_cleaner_flow(api_id: int, api_hash: str, dry_run: bool):
    sessions = session_mgr.list_sessions()
    if not sessions:
        console.print("[yellow]Hech qanday hisob ulanmagan! Avval hisob qo'shing (Menyuda 5).[/yellow]")
        return

    console.print("\n[bold]Qaysi hisobdagi botlarni tozalamoqchisiz?[/bold]")
    console.print("  [bold cyan]0.[/bold cyan] 🌐 Barcha hisoblar bo'yicha")
    for i, s in enumerate(sessions, 1):
        console.print(f"  [bold cyan]{i}.[/bold cyan] 📱 {s.stem}")

    choice = Prompt.ask("Tanlang", choices=[str(i) for i in range(len(sessions) + 1)], default="0")
    raw_months = Prompt.ask("\n[bold yellow]Necha oydan beri ishlatilmagan botlar o'chirilsin va bloklansin?[/bold yellow]", default="9")
    try:
        months_threshold = float(raw_months.strip())
    except ValueError:
        months_threshold = 9.0

    if choice == "0":
        for s in sessions:
            client = session_mgr.get_client(s.stem, api_id, api_hash)
            try:
                await client.connect()
                if await client.is_user_authorized():
                    await process_bot_cleaning(client, s.stem, months_threshold=months_threshold, dry_run=dry_run)
                else:
                    console.print(f"[red]⚠️ [{s.stem}] Sessiyasi faol emas, o'tkazib yuborildi.[/red]")
            finally:
                if client.is_connected():
                    await client.disconnect()
    else:
        selected_session = sessions[int(choice) - 1]
        client = session_mgr.get_client(selected_session.stem, api_id, api_hash)
        try:
            await client.connect()
            if await client.is_user_authorized():
                await process_bot_cleaning(client, selected_session.stem, months_threshold=months_threshold, dry_run=dry_run)
            else:
                console.print(f"[red]⚠️ [{selected_session.stem}] Sessiyasi faol emas.[/red]")
        finally:
            if client.is_connected():
                await client.disconnect()

async def run_group_cleaner_flow(api_id: int, api_hash: str, dry_run: bool):
    sessions = session_mgr.list_sessions()
    if not sessions:
        console.print("[yellow]Hech qanday hisob ulanmagan! Avval hisob qo'shing (Menyuda 5).[/yellow]")
        return

    console.print("\n[bold]Qaysi hisobdagi guruhlarni tozalamoqchisiz?[/bold]")
    console.print("  [bold cyan]0.[/bold cyan] 🌐 Barcha hisoblar bo'yicha")
    for i, s in enumerate(sessions, 1):
        console.print(f"  [bold cyan]{i}.[/bold cyan] 📱 {s.stem}")

    choice = Prompt.ask("Tanlang", choices=[str(i) for i in range(len(sessions) + 1)], default="0")
    raw_members = Prompt.ask("\n[bold yellow]Minimal a'zolar soni chegarasi (Siz yozmagan shu sondan ortiq guruhlar tozalanadi)?[/bold yellow]", default="200")
    try:
        min_members = int(raw_members.strip())
    except ValueError:
        min_members = 200

    if choice == "0":
        for s in sessions:
            client = session_mgr.get_client(s.stem, api_id, api_hash)
            try:
                await client.connect()
                if await client.is_user_authorized():
                    await process_group_cleaning(client, s.stem, min_members=min_members, dry_run=dry_run)
                else:
                    console.print(f"[red]⚠️ [{s.stem}] Sessiyasi faol emas, o'tkazib yuborildi.[/red]")
            finally:
                if client.is_connected():
                    await client.disconnect()
    else:
        selected_session = sessions[int(choice) - 1]
        client = session_mgr.get_client(selected_session.stem, api_id, api_hash)
        try:
            await client.connect()
            if await client.is_user_authorized():
                await process_group_cleaning(client, selected_session.stem, min_members=min_members, dry_run=dry_run)
            else:
                console.print(f"[red]⚠️ [{selected_session.stem}] Sessiyasi faol emas.[/red]")
        finally:
            if client.is_connected():
                await client.disconnect()

async def run_all_chats_count_flow(api_id: int, api_hash: str):
    sessions = session_mgr.list_sessions()
    if not sessions:
        console.print("[yellow]Hech qanday hisob ulanmagan! Avval hisob qo'shing (Menyuda 6).[/yellow]")
        return

    console.print("\n[bold]Qaysi hisobdagi barcha chatlarni sanamoqchisiz?[/bold]")
    console.print("  [bold cyan]0.[/bold cyan] 🌐 Barcha hisoblar bo'yicha")
    for i, s in enumerate(sessions, 1):
        console.print(f"  [bold cyan]{i}.[/bold cyan] 📱 {s.stem}")

    choice = Prompt.ask("Tanlang", choices=[str(i) for i in range(len(sessions) + 1)], default="0")
    
    sessions_to_scan = sessions if choice == "0" else [sessions[int(choice) - 1]]

    for s in sessions_to_scan:
        client = session_mgr.get_client(s.stem, api_id, api_hash)
        try:
            await client.connect()
            if not await client.is_user_authorized():
                console.print(f"[red]⚠️ [{s.stem}] Sessiyasi faol emas, o'tkazib yuborildi.[/red]")
                continue

            cleaner = ChatCleaner(client)
            console.print(f"\n[bold yellow]🔍 [{s.stem}] Akauntdagi BARCHA chatlar sanalmoqda...[/bold yellow]")

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("[cyan]Chatlar sanalmoqda...", total=None)
                stats, dialog_list = await cleaner.get_all_dialogs_summary()

            console.print(Panel(
                f"📱 [bold yellow]AKAUTDAGI JAMI CHATLAR:[/bold yellow] [bold white]{stats['total']}[/bold white] ta\n\n"
                f"  ├─ 👤 Shaxsiy chatlar: [bold cyan]{stats['users']}[/bold cyan] ta\n"
                f"  ├─ 🤖 Botlar: [bold cyan]{stats['bots']}[/bold cyan] ta\n"
                f"  ├─ 👥 Guruhlar: [bold cyan]{stats['groups']}[/bold cyan] ta\n"
                f"  └─ 📢 Kanallar: [bold cyan]{stats['channels']}[/bold cyan] ta",
                title=f"[{s.stem}] Barcha Chatlar Statistikasi",
                border_style="green"
            ))

            show_table = Confirm.ask("\n[bold yellow]Barcha chatlar ro'yxatini jadvalda ko'rishni xohlaysizmi?[/bold yellow]", default=False)
            if show_table:
                table = Table(title=f"[{s.stem}] Akauntdagi Barcha Chatlar ({len(dialog_list)} ta)", show_lines=True)
                table.add_column("№", justify="center", style="dim")
                table.add_column("Turi", style="cyan")
                table.add_column("Nomi", style="bold")
                table.add_column("Username", style="yellow")
                table.add_column("Oxirgi faollik", style="dim")
                table.add_column("O'qilmadi", justify="center", style="magenta")

                for i, d in enumerate(dialog_list, 1):
                    table.add_row(
                        str(i),
                        d["type"],
                        d["name"][:25],
                        d["username"],
                        d["date"],
                        str(d["unread"]) if d["unread"] > 0 else "-"
                    )
                console.print(table)

        finally:
            if client.is_connected():
                await client.disconnect()

async def run_categorized_chats_flow(api_id: int, api_hash: str):
    sessions = session_mgr.list_sessions()
    if not sessions:
        console.print("[yellow]Hech qanday hisob ulanmagan! Avval hisob qo'shing.[/yellow]")
        return

    console.print("\n[bold]Qaysi hisobdagi chatlarni papkalar bo'yicha saralamoqchisiz?[/bold]")
    console.print("  [bold cyan]0.[/bold cyan] 🌐 Barcha hisoblar bo'yicha")
    for i, s in enumerate(sessions, 1):
        console.print(f"  [bold cyan]{i}.[/bold cyan] 📱 {s.stem}")

    choice = Prompt.ask("Tanlang", choices=[str(i) for i in range(len(sessions) + 1)], default="0")
    
    sessions_to_scan = sessions if choice == "0" else [sessions[int(choice) - 1]]

    for s in sessions_to_scan:
        client = session_mgr.get_client(s.stem, api_id, api_hash)
        try:
            await client.connect()
            if not await client.is_user_authorized():
                console.print(f"[red]⚠️ [{s.stem}] Sessiyasi faol emas, o'tkazib yuborildi.[/red]")
                continue

            cleaner = ChatCleaner(client)
            console.print(f"\n[bold yellow]🔍 [{s.stem}] Akauntdagi chatlar papkalar (kategoriyalar) bo'yicha saralanmoqda...[/bold yellow]")

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                progress.add_task("[cyan]Saralanmoqda...", total=None)
                cat = await cleaner.categorize_all_dialogs()

            total_all = sum(len(v) for v in cat.values())

            console.print(Panel(
                f"📱 [bold yellow]AKAUTDAGI JAMI CHATLAR:[/bold yellow] [bold white]{total_all}[/bold white] ta\n\n"
                f"👑 [bold yellow]Siz Admin/Ega bo'lgan chatlar:[/bold yellow]\n"
                f"  ├─ 📢 Admin Kanallar: [bold green]{len(cat['admin_channels'])}[/bold green] ta\n"
                f"  └─ 👥 Admin Guruhlar: [bold green]{len(cat['admin_groups'])}[/bold green] ta\n\n"
                f"👤 [bold cyan]Shaxsiy chatlar va Botlar:[/bold cyan]\n"
                f"  ├─ 👤 Shaxsiy (Jonli): [bold cyan]{len(cat['personal_users'])}[/bold cyan] ta\n"
                f"  ├─ 👻 O'chirilgan Shaxsiy Hisoblar: [bold red]{len(cat['deleted_users'])}[/bold red] ta\n"
                f"  ├─ 🤖 Faol Botlar: [bold yellow]{len(cat['active_bots'])}[/bold yellow] ta\n"
                f"  └─ 🤖👻 O'chirilgan Botlar (Deleted Bot): [bold red]{len(cat['deleted_bots'])}[/bold red] ta\n\n"
                f"📢 [bold blue]Kanallar (Obunalar):[/bold blue]\n"
                f"  ├─ 🌐 Ommaviy (Public) Kanallar: [bold white]{len(cat['public_channels'])}[/bold white] ta\n"
                f"  └─ 🔒 Yopiq (Private) Kanallar: [bold dim]{len(cat['private_channels'])}[/bold dim] ta\n\n"
                f"👥 [bold magenta]Guruhlar:[/bold magenta]\n"
                f"  ├─ 🌐 Ommaviy (Public) Guruhlar: [bold white]{len(cat['public_groups'])}[/bold white] ta\n"
                f"  └─ 🔒 Yopiq (Private) Guruhlar: [bold dim]{len(cat['private_groups'])}[/bold dim] ta",
                title=f"[{s.stem}] Chatlar Papkalari Statistikasi",
                border_style="cyan"
            ))

            while True:
                console.print("\n[bold]Qaysi papka (kategoriya) chatlarini jadvalda ko'rmoqchisiz?[/bold]")
                console.print(f"  [bold cyan]1.[/bold cyan] 👑 Admin Kanallar ({len(cat['admin_channels'])} ta)")
                console.print(f"  [bold cyan]2.[/bold cyan] 👑 Admin Guruhlar ({len(cat['admin_groups'])} ta)")
                console.print(f"  [bold cyan]3.[/bold cyan] 👻 O'chirilgan Shaxsiy Hisoblar ({len(cat['deleted_users'])} ta)")
                console.print(f"  [bold cyan]4.[/bold cyan] 👤 Shaxsiy Chatlar (Jonli) ({len(cat['personal_users'])} ta)")
                console.print(f"  [bold cyan]5.[/bold cyan] 🤖 Faol Botlar ({len(cat['active_bots'])} ta)")
                console.print(f"  [bold cyan]6.[/bold cyan] 🤖👻 O'chirilgan Botlar ({len(cat['deleted_bots'])} ta)")
                console.print(f"  [bold cyan]7.[/bold cyan] 📢 Ommaviy (Public) Kanallar ({len(cat['public_channels'])} ta)")
                console.print(f"  [bold cyan]8.[/bold cyan] 🔒 Yopiq (Private) Kanallar ({len(cat['private_channels'])} ta)")
                console.print(f"  [bold cyan]9.[/bold cyan] 👥 Ommaviy (Public) Guruhlar ({len(cat['public_groups'])} ta)")
                console.print(f"  [bold cyan]10.[/bold cyan] 🔒 Yopiq (Private) Guruhlar ({len(cat['private_groups'])} ta)")
                console.print("  [bold dim]0.[/bold dim] Orqaga")

                sub_c = Prompt.ask("Tanlang", choices=[str(i) for i in range(11)], default="0")
                if sub_c == "0":
                    break

                cat_map = {
                    "1": ("👑 Admin Kanallar", cat['admin_channels']),
                    "2": ("👑 Admin Guruhlar", cat['admin_groups']),
                    "3": ("👻 O'chirilgan Shaxsiy Hisoblar", cat['deleted_users']),
                    "4": ("👤 Shaxsiy Chatlar (Jonli)", cat['personal_users']),
                    "5": ("🤖 Faol Botlar", cat['active_bots']),
                    "6": ("🤖👻 O'chirilgan Botlar", cat['deleted_bots']),
                    "7": ("📢 Ommaviy Kanallar", cat['public_channels']),
                    "8": ("🔒 Yopiq Kanallar", cat['private_channels']),
                    "9": ("👥 Ommaviy Guruhlar", cat['public_groups']),
                    "10": ("🔒 Yopiq Guruhlar", cat['private_groups']),
                }

                cat_title, cat_list = cat_map[sub_c]

                if not cat_list:
                    console.print(f"[yellow]Ushbu kategoriyada chatlar mavjud emas.[/yellow]")
                    continue

                table = Table(title=f"[{s.stem}] {cat_title} ({len(cat_list)} ta)", show_lines=True)
                table.add_column("№", justify="center", style="dim")
                table.add_column("Nomi", style="bold")
                table.add_column("Username", style="yellow")
                table.add_column("Oxirgi faollik", style="dim")
                table.add_column("O'qilmadi", justify="center", style="magenta")

                for idx, d in enumerate(cat_list, 1):
                    table.add_row(
                        str(idx),
                        d["name"][:30],
                        d["username"],
                        d["date"],
                        str(d["unread"]) if d["unread"] > 0 else "-"
                    )
                console.print(table)

        finally:
            if client.is_connected():
                await client.disconnect()

async def run_create_telegram_folders_flow(api_id: int, api_hash: str):
    sessions = session_mgr.list_sessions()
    if not sessions:
        console.print("[yellow]Hech qanday hisob ulanmagan![/yellow]")
        return

    console.print("\n[bold]Qaysi hisob Telegram ilovasida haqiqiy PAPKALAR (Folders) yaratmoqchisiz?[/bold]")
    console.print("  [bold cyan]0.[/bold cyan] 🌐 Barcha hisoblarda yaratish")
    for i, s in enumerate(sessions, 1):
        console.print(f"  [bold cyan]{i}.[/bold cyan] 📱 {s.stem}")

    choice = Prompt.ask("Tanlang", choices=[str(i) for i in range(len(sessions) + 1)], default="0")
    
    sessions_to_process = sessions if choice == "0" else [sessions[int(choice) - 1]]

    for s in sessions_to_process:
        client = session_mgr.get_client(s.stem, api_id, api_hash)
        try:
            await client.connect()
            if not await client.is_user_authorized():
                console.print(f"[red]⚠️ [{s.stem}] Sessiyasi faol emas, o'tkazib yuborildi.[/red]")
                continue

            cleaner = ChatCleaner(client)
            console.print(f"\n[bold yellow]🚀 [{s.stem}] Telegram ilovangizda haqiqiy Chat Papkalari yaratilmoqda...[/bold yellow]")

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                progress.add_task("[cyan]Papkalarni Telegramga yuborish...", total=None)
                res = await cleaner.create_telegram_folders()

            res_text = "\n".join([f"  • [bold cyan]{k}[/bold cyan]: [green]{v}[/green]" for k, v in res.items()])
            console.print(Panel(
                f"[bold green]✓ Telegram ilovangizda quyidagi PAPKALAR muvaffaqiyatli yaratildi![/bold green]\n\n{res_text}\n\n"
                f"ℹ️ [italic green]Telegram ilovangizni (Desktop yoki Mobile) ochib chap paneldagi yangi papkalarni ko'rishingiz mumkin![/italic green]",
                title=f"[{s.stem}] Telegram Papkalari Yaratildi 🚀",
                border_style="green"
            ))

        finally:
            if client.is_connected():
                await client.disconnect()

async def dry_run_menu(api_id: int, api_hash: str):
    console.print("\n[bold cyan]🔍 SKANERLASH (DRY RUN) REJIMI[/bold cyan]")
    console.print("  [bold green]1.[/bold green] 🧹 Shaxsiy chatlarni skanerlash (Bo'sh va 'Telegramga qo'shildi')")
    console.print("  [bold yellow]2.[/bold yellow] 🤖 Nofaol botlarni skanerlash (9+ oy)")
    console.print("  [bold magenta]3.[/bold magenta] 👥 Shubhali guruhlarni skanerlash (200+ a'zoli)")
    console.print("  [bold red]4.[/bold red] 👻 Faqat TEKSTLI 'Deleted Account'larni skanerlash (Media borlari saqlanadi)")
    console.print("  [bold blue]5.[/bold blue] 📁 Terminalda Chatlarni PAPKALAR bo'yicha saralash")
    console.print("  [bold cyan]6.[/bold cyan] 📊 Akauntdagi BARCHA chatlarni sanash (Umumiy statistikasi)")
    console.print("  [bold dim]0.[/bold dim] Orqaga")
    
    choice = Prompt.ask("Tanlang", choices=["0", "1", "2", "3", "4", "5", "6"], default="4")
    if choice == "1":
        await run_cleaner_flow(api_id, api_hash, dry_run=True)
    elif choice == "2":
        await run_bot_cleaner_flow(api_id, api_hash, dry_run=True)
    elif choice == "3":
        await run_group_cleaner_flow(api_id, api_hash, dry_run=True)
    elif choice == "4":
        await run_deleted_accounts_cleaner_flow(api_id, api_hash, dry_run=True)
    elif choice == "5":
        await run_categorized_chats_flow(api_id, api_hash)
    elif choice == "6":
        await run_all_chats_count_flow(api_id, api_hash)

async def delete_account_flow():
    sessions = session_mgr.list_sessions()
    if not sessions:
        console.print("[yellow]O'chirish uchun hisoblar yo'q.[/yellow]")
        return

    console.print("\n[bold]O'chirmoqchi bo'lgan hisobingizni tanlang:[/bold]")
    for i, s in enumerate(sessions, 1):
        console.print(f"  [bold red]{i}.[/bold red] {s.stem}")
    console.print("  [bold cyan]0.[/bold cyan] Orqaga")

    choice = Prompt.ask("Tanlang", choices=[str(i) for i in range(len(sessions) + 1)], default="0")
    if choice == "0":
        return

    target = sessions[int(choice) - 1]
    if Confirm.ask(f"[bold red]Haqiqatdan ham '{target.stem}' hisobini o'chirmoqchimisiz?[/bold red]"):
        if session_mgr.delete_session(target.stem):
            console.print(f"[bold green]✓ '{target.stem}' hisobi muvaffaqiyatli o'chirildi![/bold green]")

async def main():
    print_banner()
    api_id, api_hash = check_or_prompt_api_credentials()

    while True:
        console.print("\n[bold cyan]═══════════════════════════ ASOSIY MENYU ═══════════════════════════[/bold cyan]")
        console.print("  [bold green]1.[/bold green] 🧹 Bo'sh va 'Kontakt qo'shildi' chatlarni tozalash (Delete)")
        console.print("  [bold magenta]2.[/bold magenta] 🤖 9+ oy ishlatilmagan botlarni tozalash (Block & Delete)")
        console.print("  [bold yellow]3.[/bold yellow] 👥 Shubhali guruhlardan chiqish (Yozilmagan 200+ a'zoli)")
        console.print("  [bold red]4.[/bold red] 👻 Faqat TEKSTLI 'Deleted Account'larni tozalash (Rasm/Ovoz borlari SAQLANADI) 🚀 ⭐")
        console.print("  [bold green]5.[/bold green] 📂 TELEGRAM ILOVASIDA PAPKALAR (Folders) YARATISH 🚀 ⭐")
        console.print("  [bold cyan]6.[/bold cyan] 📁 Terminalda Chatlarni PAPKALAR bo'yicha saralab ko'rish")
        console.print("  [bold cyan]7.[/bold cyan] 🔍 Skanerlash (Faqat ko'rish / Dry-run)")
        console.print("  [bold blue]8.[/bold blue] 📊 Akauntdagi BARCHA chatlarni sanash (To'liq statistika)")
        console.print("  [bold white]9.[/bold white] ➕ Yangi Telegram hisob qo'shish")
        console.print("  [bold white]10.[/bold white] 📱 Ulangan hisoblar ro'yxati")
        console.print("  [bold red]11.[/bold red] 🗑️ Hisobni tizimdan o'chirish")
        console.print("  [bold dim]0.[/bold dim] 🚪 Chiqish")
        console.print("[bold cyan]═════════════════════════════════════════════════════════════════════[/bold cyan]")

        choice = Prompt.ask("Buyruqni tanlang", choices=["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11"], default="4")

        if choice == "1":
            await run_cleaner_flow(api_id, api_hash, dry_run=False)
        elif choice == "2":
            await run_bot_cleaner_flow(api_id, api_hash, dry_run=False)
        elif choice == "3":
            await run_group_cleaner_flow(api_id, api_hash, dry_run=False)
        elif choice == "4":
            await run_deleted_accounts_cleaner_flow(api_id, api_hash, dry_run=False)
        elif choice == "5":
            await run_create_telegram_folders_flow(api_id, api_hash)
        elif choice == "6":
            await run_categorized_chats_flow(api_id, api_hash)
        elif choice == "7":
            await dry_run_menu(api_id, api_hash)
        elif choice == "8":
            await run_all_chats_count_flow(api_id, api_hash)
        elif choice == "9":
            await add_new_account(api_id, api_hash)
        elif choice == "10":
            await list_accounts(api_id, api_hash)
        elif choice == "11":
            await delete_account_flow()
        elif choice == "0":
            console.print("[bold cyan]Dastur yakunlandi. Xayr![/bold cyan]")
            break

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Dastur to'xtatildi.[/yellow]")
        sys.exit(0)
