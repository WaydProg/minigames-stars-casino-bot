import aiohttp
import asyncio
from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import bot, PAYMENT_SETTINGS
from database import db
from datetime import datetime, timedelta
import json

import keyboards as kb

router = Router()

class CryptobotState(StatesGroup):
    waiting_amount = State()

async def create_cryptobot_invoice(amount_ton: float, user_id: int):
    """Создание инвойса через CryptoBot API"""
    url = f"https://pay.crypt.bot/api/createInvoice"
    
    headers = {
        "Crypto-Pay-API-Token": PAYMENT_SETTINGS["cryptobot_token"],
        "Content-Type": "application/json"
    }
    
    payload = {
        "asset": PAYMENT_SETTINGS["cryptobot_currency"],
        "amount": str(amount_ton),
        "description": f"Пополнение баланса для пользователя {user_id}",
        "hidden_message": f"user_id:{user_id}",
        "paid_btn_name": "callback",
        "paid_btn_url": "https://t.me/@dicelite_bot",
        "payload": f"deposit_{user_id}_{amount_ton}",
        "allow_comments": False,
        "allow_anonymous": False,
        "expires_in": PAYMENT_SETTINGS["payment_timeout"]
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                data = await response.json()
                if data.get("ok"):
                    return data["result"]
                else:
                    print(f"CryptoBot error: {data}")
                    return None
    except Exception as e:
        print(f"CryptoBot API error: {e}")
        return None

async def check_cryptobot_invoice(invoice_id: str):
    """Проверка статуса инвойса CryptoBot"""
    url = f"https://pay.crypt.bot/api/getInvoices?invoice_ids={invoice_id}"
    
    headers = {
        "Crypto-Pay-API-Token": PAYMENT_SETTINGS["cryptobot_token"]
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                data = await response.json()
                if data.get("ok") and data["result"]["items"]:
                    return data["result"]["items"][0]
                return None
    except Exception as e:
        print(f"CryptoBot check error: {e}")
        return None

@router.callback_query(F.data == "pay_method_cryptobot")
async def select_cryptobot_method(callback: CallbackQuery):
    await callback.message.edit_text(
        "💎 Пополнение через Cryptobot (TON)\n\n"
        "Выберите пакет пополнения:\n"
        "• 25 звезд = 0.125 TON\n"  # Добавлена строка
        "• 50 звезд = 0.25 TON\n"
        "• 100 звезд = 0.5 TON\n"
        "• 200 звезд = 1 TON\n"
        "• 500 звезд = 2 TON\n\n"
        "💰 Актуальный курс: 1 TON = 200 звезд",
        reply_markup=kb.cryptobot_packages_menu()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("crypto_"))
async def process_cryptobot_package(callback: CallbackQuery):
    package = callback.data.split("_")[1]
    packages = {"25": 25, "50": 50, "100": 100, "200": 200, "500": 500}  # Добавлен пакет 25
    
    if package not in packages:
        await callback.answer("❌ Неверный пакет")
        return
    
    amount_stars = packages[package]
    amount_ton = amount_stars / 200  # 1 TON = 200 звезд
    
    # Создаем инвойс в Cryptobot
    invoice = await create_cryptobot_invoice(amount_ton, callback.from_user.id)
    
    if not invoice:
        await callback.message.edit_text(
            "❌ Ошибка при создании платежа\n\n"
            "Попробуйте позже или выберите другой способ оплаты",
            reply_markup=kb.payment_methods_menu()
        )
        return
    
    # Сохраняем платеж в базу
    payment = await db.create_cryptobot_payment(
        callback.from_user.id,
        amount_ton,
        amount_stars,
        invoice["invoice_id"]
    )
    
    await callback.message.edit_text(
        f"💎 Пополнение на {amount_stars} звезд\n\n"
        f"💰 Сумма к оплате: {amount_ton} TON\n"
        f"⏰ Время на оплату: 30 минут\n\n"
        f"Нажмите кнопку ниже для оплаты:",
        reply_markup=kb.cryptobot_payment_keyboard(invoice["pay_url"])
    )
    await callback.answer()

@router.callback_query(F.data == "check_crypto_payment")
async def check_crypto_payment(callback: CallbackQuery):
    # Получаем последний pending платеж пользователя
    payment = await db.get_last_cryptobot_payment(callback.from_user.id)
    
    if not payment:
        await callback.answer("❌ Платеж не найден")
        return
    
    # Проверяем статус в Cryptobot
    invoice = await check_cryptobot_invoice(payment.invoice_id)
    
    if not invoice:
        await callback.answer("❌ Ошибка проверки платежа")
        return
    
    if invoice["status"] == "paid":
        # Зачисляем средства
        new_balance = await db.update_balance(
            callback.from_user.id,
            payment.amount_stars,
            "deposit",
            f"Пополнение через Cryptobot: {payment.amount_stars} звезд"
        )
        
        # Обновляем статус платежа
        await db.update_cryptobot_payment(payment.id, "paid")
        
        await callback.message.edit_text(
            f"✅ Оплата подтверждена!\n\n"
            f"💎 Зачислено: {payment.amount_stars} звезд\n"
            f"📊 Новый баланс: {new_balance} звезд\n\n"
            f"Приятной игры! 🎰"
        )
    elif invoice["status"] == "expired":
        await db.update_cryptobot_payment(payment.id, "expired")
        await callback.message.edit_text(
            "❌ Время оплаты истекло\n\n"
            "Создайте новый платеж",
            reply_markup=kb.payment_methods_menu()
        )
    else:
        await callback.answer("⏳ Платеж еще не поступил")
    
    await callback.answer()

@router.callback_query(F.data == "cancel_crypto_payment")
async def cancel_crypto_payment(callback: CallbackQuery):
    await callback.message.edit_text(
        "❌ Платеж отменен\n\n"
        "Выберите способ оплаты:",
        reply_markup=kb.payment_methods_menu()
    )
    await callback.answer()