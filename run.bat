@echo off
chcp 65001 > nul
title 🧹 Telegram Cleaner Pro

echo ================================================================
echo   🧹 Telegram Cleaner Pro — Hisoblarni tozalash vositasi
echo ================================================================
echo.

:: 1. Python o'rnatilganligini tekshirish
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

:: 2. Agar Python topilmasa, avtomatik o'rnatish (Winget yoki PowerShell orqali)
if "%PYTHON_CMD%"=="" (
    echo [OGOHLANTIRISH] Kompyuteringizda Python topilmadi!
    echo.
    echo 🔄 Python avtomatik tarzda yuklab olinmoqda va o'rnatilmoqda...
    echo Iltimos, 1-2 daqiqa kuting...
    echo.

    :: Winget orqali o'rnatishga urinish (Windows 10/11 da tayyor bo'ladi)
    winget --version >nul 2>&1
    if %errorlevel% equ 0 (
        winget install --id Python.Python.3.12 -e --accept-package-agreements --accept-source-agreements --silent
    ) else (
        :: Agar winget bo'lmasa, PowerShell orqali rasmiy Python o'rnatgichni yuklab ishga tushirish
        powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.3/python-3.12.3-amd64.exe' -OutFile '%temp%\python_installer.exe'"
        start /wait %temp%\python_installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_pip=1
        del %temp%\python_installer.exe
    )

    echo.
    echo [✓] Python o'rnatildi! Dasturni davom ettirish uchun ushbu oynani yoping va 'run.bat' ni qayta bosing.
    echo.
    pause
    exit /b
)

:: 3. Virtual muhit yaratish yoki faollashtirish
if not exist "venv\Scripts\python.exe" (
    echo [1/2] 📦 Kutubxonalar o'rnatilmoqda (faqat birinchi marta 1 daqiqa vaqt oladi)...
    %PYTHON_CMD% -m venv venv
    venv\Scripts\python.exe -m pip install --upgrade pip >nul 2>&1
    venv\Scripts\python.exe -m pip install -r requirements.txt
    echo [2/2] ✓ Tayyor!
    echo.
)

:: 4. Dasturni ishga tushirish
venv\Scripts\python.exe main.py

if %errorlevel% neq 0 (
    echo.
    echo Dasturda xatolik yuz berdi yoki to'xtatildi.
    pause
)
