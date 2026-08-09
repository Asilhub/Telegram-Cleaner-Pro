# 🧹 Telegram Cleaner Pro — Telegram Tozalovchi Userbot

<p align="center">
  <img src="https://img.shields.io/badge/Windows-10%20%2F%2011-0078D6?style=for-the-badge&logo=windows&logoColor=white" />
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Telegram-MTProto-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" />
</p>

Telegram hisoblaringizdagi keraksiz **"Falonchi Telegram'ga qo'shildi"** (Contact joined) xabarlarini, **bo'sh qolib ketgan chatlarni** va **9+ oydan beri ishlatilmagan nofaol botlarni** bir zumda avtomatik tozalab beruvchi qulay va xavfsiz vosita.

Dasturlashni bilish umuman shart emas — Windows'da `run.bat` ni bossangiz bas! 🚀

---

## 💻 Windows Uchun O'rnatish va Ishga Tushirish (3 Qadamda)

> [!TIP]
> **API ID va API HASH kiritish shart emas!** Dastur ichida barchasi tayyor sozlangan.

### 1-Qadam. Loyihani yuklab oling
Quyidagi tugmani bosing va ZIP arxivni kompyuteringizga yuklab oling:
👉 [**⬇️ Telegram-Cleaner-Pro (ZIP) Yuklab Olish**](https://github.com/Asilhub/Telegram-Cleaner-Pro/archive/refs/heads/main.zip)

Yuklab olingan `.zip` faylni ustiga sichqonchaning o'ng tugmasini bosib, **"Извлечь все..." (Extract all / Arxivdan chiqarish)** ni bosing.

---

### 2-Qadam. `run.bat` ni ishga tushiring
Arxivdan chiqqan papka ichiga kiring va **`run.bat`** fayliga sichqoncha bilan 2 marta bosing.

> [!NOTE]
> Agar kompyuteringizda Python o'rnatilmagan bo'lsa:
> 1. [python.org/downloads](https://www.python.org/downloads/) saytidan Python'ni yuklab oling.
> 2. O'rnatish paytida eng pastdagi **"Add python.exe to PATH"** katakchasiga albatta belgi qo'ying!

---

### 3-Qadam. Hisobingizni tozalang!
Dastur oynasi ochilgach:
1. **`4`** ni tanlang va telefon raqamingizni kiriting.
2. Telegramga kelgan kodni yozing (hisob ulanadi).
3. Kerakli buyruqni tanlang:
   - **`1`** — 🧹 Bo'sh chatlar va "Telegramga qo'shildi" xabarlarini tozalash.
   - **`2`** — 🤖 9+ oy ishlatilmagan botlarni bloklash va o'chirish.
   - **`3`** — 🔍 O'chirishdan oldin chatlarni ko'rib chiqish (Dry Run).

---

## ✨ Asosiy Imkoniyatlar

- 📌 **"Telegramga qo'shildi" bildirishnomalarini tozalash**: Kontaktlaringiz ro'yxatidan ochilib qolgan keraksiz lichkalarni o'chiradi.
- 📭 **Bo'sh chatlarni tozalash**: Hech qanday xabar almashilmagan (0 ta xabar) barcha shaxsiy chatlarni topib o'chiradi.
- 🤖 **Nofaol Botlarni Tozalash (Block & Delete)**: 9 oy (yoki o'zingiz kiritgan muddat) davomida ishlatilmagan botlarni bloklaydi va chatlarini tozalaydi.
- 👥 **Ko'p hisobli (Multi-Account)**: Bir vaqtning o'zida istalgancha Telegram profilingizni ulab, navbat bilan tozalashingiz mumkin.
- ⚡️ **O'ta Tezkor (High Speed)**: Yozishmasi bor (3+ xabar) bo'lgan barcha oddiy chatlarni darhol o'tkazib yuboradi (1000 ta chatni bir necha soniyada skanerlaydi).
- 🛡️ **Xavfsiz**:
  - Shaxsiy sessiyalaringiz faqat o'zingizning kompyuteringizda saqlanadi.
  - Muhim guruhlar, kanallar va "Saqlangan xabarlar" (Saved Messages)ga **mutlaqo teginmaydi**.

---

## 🐧 Linux / macOS yoki Termux Foydalanuvchilari Uchun

```bash
git clone https://github.com/Asilhub/Telegram-Cleaner-Pro.git
cd Telegram-Cleaner-Pro
chmod +x run.sh
./run.sh
```

---

## 🔒 Xavfsizlik Kafolati

- Dastur butunlay **Open Source (Ochiq kodli)**.
- Barcha hisob sessiyalari faqat sizning kompyuteringizdagi `sessions/` papkasida qoladi, hech qanday begona serverlarga yuborilmaydi.

---

## 👨‍💻 Muallif

- **GitHub**: [@Asilhub](https://github.com/Asilhub)

Loyiha foydali bo'lgan bo'lsa, GitHub'da ⭐️ **Star** tugmasini bosib qo'llab-quvvatlang!
