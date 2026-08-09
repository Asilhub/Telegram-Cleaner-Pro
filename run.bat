@echo off
chcp 65001 > nul
title 🧹 Telegram Cleaner Pro

echo ================================================================
echo   🧹 Telegram Cleaner Pro — Hisoblarni tozalash vositasi
echo ================================================================
echo.

:: Python tekshiruvi (python yoki py launcher)
set PYTHON_CMD=
python --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=python
) else (
    py --version >nul 2>&1
    if %errorlevel% equ 0 (
        set PYTHON_CMD=py
    )
)

if "%PYTHON_CMD%"=="" (
    echo [XATO] Kompyuteringizda Python topilmadi!
    echo.
    echo 1. https://www.python.org/downloads/ saytiga kiring va Python yuklab oling.
    echo 2. O'rnatish paytida "Add python.exe to PATH" katakchasiga belgi qo'ying!
    echo.
    pause
    exit /b
)

:: Virtual muhit yaratish yoki faollashtirish
if not exist "venv\Scripts\python.exe" (
    echo [1/2] 📦 Kutubxonalar o'rnatilmoqda (faqat birinchi marta 1-2 daqiqa vaqt oladi)...
    %PYTHON_CMD% -m venv venv
    venv\Scripts\python.exe -m pip install --upgrade pip >nul 2>&1
    venv\Scripts\python.exe -m pip install -r requirements.txt
    echo [2/2] ✓ O'rnatish muvaffaqiyatli yakunlandi!
    echo.
)

:: Dasturni ishga tushirish
venv\Scripts\python.exe main.py

if %errorlevel% neq 0 (
    echo.
    echo Dasturda xatolik yuz berdi.
    pause
)
