# 🧹 Telegram Cleaner Pro — Telegram Tozalovchi Userbot

<p align="center">
  <img src="https://img.shields.io/badge/Windows-10%20%2F%2011-0078D6?style=for-the-badge&logo=windows&logoColor=white" />
  <img src="https://img.shields.io/badge/Linux-Ubuntu%20%2F%20Debian-FCC624?style=for-the-badge&logo=linux&logoColor=black" />
  <img src="https://img.shields.io/badge/macOS-Apple-000000?style=for-the-badge&logo=apple&logoColor=white" />
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Telegram-MTProto-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white" />
</p>

Telegram hisoblaringizdagi keraksiz **"Falonchi Telegram'ga qo'shildi"** (Contact joined) xabarlarini, **bo'sh qolib ketgan chatlarni** va **9+ oydan beri ishlatilmagan nofaol botlarni** bir zumda avtomatik tozalab beruvchi qulay va xavfsiz vosita.

Dasturlashni bilish shart emas — **Windows**da `run.bat`, **Linux**da `run.sh` orqali 1 ta tugma bilan ishga tushadi! 🚀

---

## ✨ Asosiy Imkoniyatlar

- 📌 **"Telegramga qo'shildi" bildirishnomalarini tozalash**: Kontaktlaringiz ro'yxatidan ochilib qolgan keraksiz lichkalarni o'chiradi.
- 📭 **Bo'sh chatlarni tozalash**: Hech qanday xabar almashilmagan (0 ta xabar) barcha shaxsiy chatlarni topib o'chiradi.
- 🤖 **Nofaol Botlarni Tozalash (Block & Delete)**: 9 oy (yoki o'zingiz kiritgan muddat) davomida ishlatilmagan botlarni bloklaydi va chatlarini tozalaydi.
- 👥 **Ko'p hisobli (Multi-Account)**: Bir vaqtning o'zida istalgancha Telegram profilingizni ulab, navbat bilan tozalashingiz mumkin.
- ⚡️ **O'ta Tezkor (High Speed)**: Yozishmasi bor (3+ xabar) bo'lgan barcha chatlarni xotiraning o'zida bir zumda o'tkazib yuboradi (1000 ta chatni bir necha soniyada skanerlaydi).
- 🔍 **Sinov (Dry Run) Rejimi**: O'chirishdan oldin topilgan barcha chatlar va botlar ro'yxatini jadvalda ko'rsatib, tasdiqlashingizni so'raydi.
- 🛡️ **Xavfsiz**:
  - Shaxsiy sessiyalaringiz faqat o'zingizning qurilmangizda saqlanadi.
  - Guruhlar, kanallar va "Saqlangan xabarlar" (Saved Messages)ga **mutlaqo teginmaydi**.

---

## 🚀 Qanday Ishga Tushiriladi? (Qo'llanma)

> [!TIP]
> **API ID va API HASH kiritish shart emas!** Dastur ichida barchasi tayyor sozlangan.

---

### 🪟 1. Windows Kompyuter Uchun (Juda Oson)

1. Loyihani yuklab oling:  
   👉 [**⬇️ Telegram-Cleaner-Pro (ZIP) Yuklab Olish**](https://github.com/Asilhub/Telegram-Cleaner-Pro/archive/refs/heads/main.zip)
2. ZIP arxivni papkaga chiqaring (**Extract all / Arxivdan chiqarish**).
3. Papka ichidagi **`run.bat`** fayliga sichqoncha bilan 2 marta bosing.

*(Agar kompyuteringizda Python bo'lmasa, [python.org](https://www.python.org/downloads/) dan yuklab o'rnatayotganda **"Add python.exe to PATH"** belgisini qo'yishni unutmang).*

---

### 🐧 2. Linux (Ubuntu / Debian / CentOS) va macOS Uchun

Terminalni oching va quyidagi buyruqni bering:

```bash
git clone https://github.com/Asilhub/Telegram-Cleaner-Pro.git
cd Telegram-Cleaner-Pro
chmod +x run.sh
./run.sh
```

*(Dastur virtual muhitni yaratib, kutubxonalarni o'zi o'rnatadi va asosiy menyuni ochadi).*

---

### 📱 3. Android (Termux) Uchun

Termux ilovasida quyidagi buyruqlarni kiriting:

```bash
pkg update && pkg install git python -y
git clone https://github.com/Asilhub/Telegram-Cleaner-Pro.git
cd Telegram-Cleaner-Pro
bash run.sh
```

---

## 📋 Dastur Menyusidan Foydalanish

Dastur ishga tushgach, quyidagi boshqaruv paneli chiqadi:

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

1. **4-band**ni tanlab, telefon raqamingizni kiriting va Telegramga kelgan kod orqali hisobingizni ulang.
2. Hisobingiz ulangach:
   - **`1`** — Bo'sh chatlar va "Telegramga qo'shildi" lichkalarni tozalash.
   - **`2`** — 9 oydan beri ishlatilmagan botlarni bloklash va o'chirish.
   - **`3`** — O'chirishdan oldin chatlar va botlarni ko'rib chiqish (Dry Run).

---

## 🔒 Xavfsizlik Kafolati

- Dastur butunlay **Open Source (Ochiq kodli)**.
- Barcha hisob sessiyalari (`.session`) faqat sizning qurilmangizdagi `sessions/` papkasida qoladi, hech qanday serverlarga yuborilmaydi.
- `.gitignore` sozlangan bo'lib, hisoblaringiz internetga chiqib ketishidan himoyalangan.

---

## 👨‍💻 Muallif

- **GitHub**: [@Asilhub](https://github.com/Asilhub)

Loyiha sizga ma'qul kelgan bo'lsa, GitHub'da ⭐️ **Star** bosib qo'llab-quvvatlang!
