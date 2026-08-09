@echo off
chcp 65001 > nul
title Telegram Cleaner Pro

echo ====================================================
echo   🧹 Telegram Cleaner Userbot ishga tushirilmoqda...
echo ====================================================

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [XATO] Kompyuteringizda Python topilmadi!
    echo Iltimos, https://www.python.org saytidan Python o'rnating va "Add Python to PATH" katakchasini belgilang.
    pause
    exit /b
)

if not exist venv (
    echo [INFO] Kutubxonalar o'rnatilmoqda...
    python -m venv venv
    call venv\Scripts\activate
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate
)

python main.py
pause
