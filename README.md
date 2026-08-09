# 🧹 Telegram Cleaner Pro — Telegram Tozalovchi Userbot

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Telegram-MTProto-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" />
</p>

Telegram hisoblaringizdagi keraksiz **"Falonchi Telegram'ga qo'shildi"** (Contact joined) xabarlarini, **bo'sh qolib ketgan chatlarni** va **9+ oydan beri ishlatilmagan nofaol botlarni** bir zumda avtomatik tozalab beruvchi qulay va xavfsiz vosita.

Dasturlashni bilish shart emas — 1 ta buyruq bilan ishga tushadi! 🚀

---

## ✨ Imkoniyatlari

- 📌 **"Telegramga qo'shildi" bildirishnomalarini tozalash**: Kontaktlaringiz ro'yxatidan ochilib qolgan keraksiz lichkalarni o'chiradi.
- 📭 **Bo'sh chatlarni tozalash**: Hech qanday xabar almashilmagan (0 ta xabar) barcha shaxsiy chatlarni topib o'chiradi.
- 🤖 **Nofaol Botlarni Tozalash (Block & Delete)**: 9 oy (yoki o'zingiz kiritgan muddat) davomida ishlatilmagan botlarni bloklaydi va chatlarini tozalaydi.
- 👥 **Ko'p hisobli (Multi-Account)**: Bir vaqtning o'zida istalgancha Telegram profilingizni ulab, tozalashingiz mumkin.
- ⚡️ **O'ta Tezkor (High Speed)**: Chatlardagi xabarlar soni 3 tadan ko'p bo'lsa, xotiraning o'zida bir zumda o'tkazib yuboradi (1000 ta chatni bir necha soniyada skanerlaydi).
- 🔍 **Sinov (Dry Run) Rejimi**: O'chirishdan oldin topilgan barcha chatlar va botlar ro'yxatini jadvalda ko'rsatib, tasdiqlashingizni so'raydi.
- 🛡️ **Xavfsiz**:
  - Shaxsiy sessiyalaringiz faqat o'zingizning qurilmangizda saqlanadi.
  - Guruhlar, kanallar va "Saqlangan xabarlar" (Saved Messages)ga **mutlaqo teginmaydi**.

---

## 🚀 Qanday Ishga Tushiriladi? (Oddiy Qo'llanma)

> [!TIP]
> **API ID va API HASH kiritish shart emas!** Dastur ichida barchasi tayyor sozlangan. Sizdan faqat telefon raqam va Telegram kodi so'raladi.

### 💻 1. Windows kompyuterda:
1. Ushbu loyihani yuklab oling (yashil **Code** -> **Download ZIP**) va arxivdan chiqaring.
2. Papka ichidagi **`run.bat`** fayliga sichqoncha bilan 2 marta bosing.
3. Bo'ldi! Dastur kerakli kutubxonalarni o'zi o'rnatib, menyuni ochadi.

---

### 🐧 2. Linux / macOS kompyuterda:
Terminalni oching va quyidagi buyruqlarni ketma-ket nusxalab tashlang:

```bash
git clone https://github.com/Asilhub/Telegram-Cleaner-Pro.git
cd Telegram-Cleaner-Pro
chmod +x run.sh
./run.sh
```

---

### 📱 3. Android (Termux) orqali:
Telefonda Termux ilovasini ochib quyidagilarni kiriting:

```bash
pkg update && pkg install git python -y
git clone https://github.com/Asilhub/Telegram-Cleaner-Pro.git
cd Telegram-Cleaner-Pro
bash run.sh
```

---

## 📋 Dasturdan Foydalanish Qadamlari

Dastur ishga tushgach, chiroyli boshqaruv menyusi chiqadi:

```text
═══════════════════════ ASOSIY MENYU ═══════════════════════
  1. 🧹 Bo'sh va 'Kontakt qo'shildi' chatlarni tozalash (Delete)
  2. 🤖 9+ oy ishlatilmagan botlarni tozalash (Block & Delete)
  3. 🔍 Skanerlash (Faqat ko'rish / Dry-run)
  4. ➕ Yangi Telegram hisob qo'shish
  5. 📱 Ulangan hisoblar ro'yxati
  6. 🗑️ Hisobni tizimdan o'chirish
  0. 🚪 Chiqish
═════════════════════════════════════════════════════════════
```

1. **4-band**ni tanlab, telefon raqamingizni kiriting va Telegramga kelgan kodni yozing.
2. Hisobingiz ulangach:
   - **`1`** ni bossangiz — barcha bo'sh chatlar va "Telegramga qo'shildi" lichkalar tozalanadi.
   - **`2`** ni bossangiz — 9 oydan beri ishlatilmagan botlar tozalanadi.
   - **`3`** ni bossangiz — o'chirmasdan faqat ro'yxatni ko'rib chiqishingiz mumkin.

---

## 🔒 Xavfsizlik

- Barcha `.session` fayllar faqat sizning mahalliy kompyuteringizdagi `sessions/` papkasida saqlanadi.
- Git tizimida `.gitignore` sozlangan bo'lib, sizning hisobingiz ma'lumotlari yoki shaxsiy sessiyalaringiz internetga chiqib ketmaydi.

---

## 👨‍💻 Muallif va Kanal

- **GitHub**: [@Asilhub](https://github.com/Asilhub)
- **Telegram Kanal**: [@Kanal_Usernamengiz](https://t.me/Kanal_Usernamengiz) *(Kanal havolangizni qo'yishingiz mumkin)*

Agar loyiha sizga yoqqan bo'lsa, GitHub'da ⭐️ **Star** bosishni unutmang!
