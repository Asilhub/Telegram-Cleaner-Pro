#!/usr/bin/env bash

# Ranglar
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${CYAN}====================================================${NC}"
echo -e "${YELLOW}  🧹 Telegram Cleaner Userbot ishga tushirilmoqda...${NC}"
echo -e "${CYAN}====================================================${NC}"

# Python o'rnatilganligini tekshirish
if ! command -v python3 &> /dev/null; then
    echo -e "❌ Python3 topilmadi! Iltimos, Python o'rnating."
    exit 1
fi

# Virtual muhitni tekshirish yoki yaratish
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}📦 Birinchi marta ishga tushirilmoqda: Kutubxonalar o'rnatilmoqda...${NC}"
    python3 -m venv venv
    ./venv/bin/pip install --upgrade pip > /dev/null 2>&1
    ./venv/bin/pip install -r requirements.txt
fi

# Dasturni ishga tushirish
./venv/bin/python main.py
