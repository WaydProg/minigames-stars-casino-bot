from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN1')
PAYMENT_PROVIDER_TOKEN = os.getenv('PAYMENT_PROVIDER_TOKEN1')
CRYPTOBOT_TOKEN = os.getenv('CRYPTOBOT_TOKEN1')
ADMIN_IDS = [1473795067, 5145429773, 6446981309]
HISTORY_CHAT_ID = os.getenv('HISTORY_CHAT_ID1')
WITHDRAWAL_CHAT_ID = os.getenv('WITHDRAWAL_CHAT_ID1')

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML), request_timeout=120)
dp = Dispatcher()

# Настройки игр
GAME_SETTINGS = {
    "dice_win_chance": 0.4,
    "dart_win_chance": 0.4,
    "basketball_win_chance": 0.4,
    "football_win_chance": 0.4,
    "bowling_win_chance": 0.4,
    "slot_win_chance": 0.3,
    "min_bet": 1,
    "max_bet": 1000
}

GAME_COSTS = {
    "dice": 5, 
    "dart": 5, 
    "basketball": 5, 
    "football": 5, 
    "bowling": 5, 
    "slot": 10
}

WIN_MULTIPLIERS = {
    "dice": 2.5, 
    "dart": 2.5, 
    "basketball": 2.5, 
    "football": 2.5, 
    "bowling": 2.5, 
    "slot": 3.5
}

PAYMENT_SETTINGS = {
    "cryptobot_token": CRYPTOBOT_TOKEN,  
    "cryptobot_currency": "TON",  # Валюта для Cryptobot
    "ton_to_stars_rate": 1,  # Курс: 1 TON = X звезд
    "min_deposit": 50,  # Минимальное пополнение
    "payment_timeout": 1800  # Время на оплату в секундах (30 минут)
}