# 🧹 Telegram Cleaner Pro — Telegram Tozalovchi Userbot

<p align="center">
  <img src="https://img.shields.io/badge/Windows-10%20%2F%2011-0078D6?style=for-the-badge&logo=windows&logoColor=white" />
  <img src="https://img.shields.io/badge/Linux-Ubuntu%20%2F%20Debian-FCC624?style=for-the-badge&logo=linux&logoColor=black" />
  <img src="https://img.shields.io/badge/macOS-Apple-000000?style=for-the-badge&logo=apple&logoColor=white" />
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Telegram-MTProto-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white" />
</p>

Telegram hisoblaringizdagi:
- 📌 **"Falonchi Telegram'ga qo'shildi"** servis bildirishnomalari
- 📭 **Bo'sh qolib ketgan chatlar**
- 🤖 **9+ oydan beri ishlatilmagan nofaol botlar**
- 👥 **Siz xabar yozmagan, majburiy qo'shib yuborilgan shubhali guruhlar (200+ a'zoli)**

barchasini avtomatik aniqlab, bir zumda tozalab beruvchi qulay va xavfsiz Userbot vositasi.

Dasturlashni bilish shart emas — **Windows**da `run.bat`, **Linux**da `run.sh` orqali 1 ta tugma bilan ishga tushadi! 🚀

---

## ✨ Asosiy Imkoniyatlar

1. 👥 **Shubhali va Keraksiz Guruhlarni Tozalash**:
   - Sizni kimdir majburlab qo'shib yuborgan, o'zingiz biror marta xabar yozmagan 200+ a'zoli guruhlardan avtomatik chiqadi va o'chiradi.
   - *O'zingiz yaratgan (Creator) yoki Admin bo'lgan guruhlarga mutlaqo teginmaydi!*
2. 🤖 **Nofaol Botlarni Tozalash (Block & Delete)**:
   - 9 oy (yoki o'zingiz kiritgan muddat) davomida ishlatilmagan botlarni bloklaydi va chatlarini tozalaydi.
3. 📌 **"Telegramga qo'shildi" xabarlarini tozalash**:
   - Kontaktlar ro'yxatidan ochilib qolgan keraksiz lichkalarni o'chiradi.
4. 📭 **Bo'sh chatlarni tozalash**:
   - Hech qanday xabar almashilmagan (0 ta xabar) barcha shaxsiy chatlarni topib o'chiradi.
5. 👥 **Ko'p hisobli (Multi-Account)**:
   - Bir vaqtning o'zida istalgancha Telegram profilingizni ulab, navbat bilan tozalashingiz mumkin.
6. ⚡️ **O'ta Tezkor (High Speed)**:
   - Yozishmasi bor (3+ xabar) bo'lgan barcha chatlarni bir zumda o'tkazib yuboradi (1000 ta chatni bir necha soniyada skanerlaydi).
7. 🔍 **Sinov (Dry Run) Rejimi**:
   - O'chirishdan oldin topilgan barcha chatlar, botlar va guruhlar ro'yxatini jadvalda ko'rsatib, tasdiqlashingizni so'raydi.

---

## 🚀 Qanday Ishga Tushiriladi?

> [!TIP]
> **API ID va API HASH kiritish shart emas!** Dastur ichida barchasi tayyor sozlangan.

### 🪟 1. Windows Kompyuter Uchun
1. Loyihani yuklab oling:  
   👉 [**⬇️ Telegram-Cleaner-Pro (ZIP) Yuklab Olish**](https://github.com/Asilhub/Telegram-Cleaner-Pro/archive/refs/heads/main.zip)
2. ZIP arxivni papkaga chiqaring (**Extract all / Arxivdan chiqarish**).
3. Papka ichidagi **`run.bat`** fayliga sichqoncha bilan 2 marta bosing.

*(Agar Python o'rnatilmagan bo'lsa, [python.org](https://www.python.org/downloads/) dan o'rnatayotganda **"Add python.exe to PATH"** belgisini qo'ying).*

---

### 🐧 2. Linux (Ubuntu / Debian) va macOS Uchun

Terminalda quyidagi buyruqni bering:

```bash
git clone https://github.com/Asilhub/Telegram-Cleaner-Pro.git
cd Telegram-Cleaner-Pro
chmod +x run.sh
./run.sh
```

---

### 📱 3. Android (Termux) Uchun

```bash
pkg update && pkg install git python -y
git clone https://github.com/Asilhub/Telegram-Cleaner-Pro.git
cd Telegram-Cleaner-Pro
bash run.sh
```

---

## 📋 Dastur Menyusidan Foydalanish

Dastur ochilganda:

```text
═══════════════════════════ ASOSIY MENYU ═══════════════════════════
  1. 🧹 Bo'sh va 'Kontakt qo'shildi' chatlarni tozalash (Delete)
  2. 🤖 9+ oy ishlatilmagan botlarni tozalash (Block & Delete)
  3. 👥 Shubhali guruhlardan chiqish (Yozilmagan 200+ a'zoli)
  4. 🔍 Skanerlash (Faqat ko'rish / Dry-run)
  5. ➕ Yangi Telegram hisob qo'shish
  6. 📱 Ulangan hisoblar ro'yxati
  7. 🗑️ Hisobni tizimdan o'chirish
  0. 🚪 Chiqish
═════════════════════════════════════════════════════════════════════
```

1. **5-band** orqali hisobingizni ulang.
2. Kerakli bandni tanlang:
   - **`1`** — Bo'sh chatlar va kontakt xabarlarini tozalash.
   - **`2`** — 9 oydan beri ishlatilmagan botlarni tozalash.
   - **`3`** — Siz umuman xabar yozmagan 200+ a'zoli keraksiz guruhlardan chiqish.
   - **`4`** — Skanerlash (faqat ko'rib chiqish).

---

## 🔒 Xavfsizlik Kafolati

- Dastur butunlay **Open Source (Ochiq kodli)**.
- Barcha hisob sessiyalari (`.session`) faqat sizning qurilmangizdagi `sessions/` papkasida qoladi, hech qanday serverga yuborilmaydi.
- `.gitignore` sozlangan bo'lib, hisoblaringiz internetga chiqib ketishidan to'liq himoyalangan.

---

## 👨‍💻 Muallif

- **GitHub**: [@Asilhub](https://github.com/Asilhub)

⭐️ Loyiha ma'qul kelgan bo'lsa, GitHub'da Star bosishni unutmang!
