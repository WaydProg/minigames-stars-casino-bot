from aiogram.types import LabeledPrice, Message, PreCheckoutQuery
from aiogram.filters import Command
from config import bot
from database import db
from botlogic.keyboards.payment_keyboard import payment_keyboard

async def send_invoice_handler(message: Message, amount: int = 25):  # Значение по умолчанию 25
    prices = [LabeledPrice(label="XTR", amount=amount)]
    
    await message.answer_invoice(
        title=f"Пополнение баланса на {amount} звезд",
        description=f"Пополнение игрового баланса на {amount} звезд",
        prices=prices,
        provider_token="",  # Для Telegram Stars оставляем пустую строку
        payload=f"deposit_{message.from_user.id}_{amount}",
        currency="XTR",
        reply_markup=payment_keyboard(amount),
    )

async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)

async def success_payment_handler(message: Message):
    payment_info = message.successful_payment
    stars_amount = payment_info.total_amount
    payload = payment_info.invoice_payload
    
    # Зачисляем средства на баланс
    new_balance = await db.update_balance(
        message.from_user.id,
        stars_amount,
        "deposit",
        f"Пополнение через Stars: {stars_amount} звезд"
    )
    
    await message.answer(
        f"🥳 Спасибо за пополнение! 🤗\n\n"
        f"💎 Зачислено: {stars_amount} звезд\n"
        f"📊 Новый баланс: {new_balance} звезд\n\n"
        f"Приятной игры! 🎰"
    )

async def pay_support_handler(message: Message):
    await message.answer(
        text="💫 Поддержка по платежам\n\n"
        "Если у вас возникли проблемы с пополнением баланса:\n"
        "• Проверьте, достаточно ли у вас Telegram Stars\n"
        "• Убедитесь, что бот не заблокирован\n"
        "• Для возврата средств свяжитесь с администратором\n\n"
        "👤 Администратор: @username_администратора\n"
        "⏰ Время ответа: в течение 24 часов"
    )