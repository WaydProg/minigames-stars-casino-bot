from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from config import dp, bot
from database import db
import keyboards as kb
from game_handlers import router as game_router
from admin_panel import router as admin_router
from payment_handlers import router as payment_router
import asyncio
import logging
from handlers.referral import router as referral_router
from handlers.cryptobot_handler import router as cryptobot_router
from aiogram.types import FSInputFile

# Регистрируем роутеры
dp.include_router(game_router)
dp.include_router(admin_router)
dp.include_router(payment_router)
dp.include_router(referral_router)
dp.include_router(cryptobot_router)

@dp.message(CommandStart())
async def start_command(message: Message):
    path_to_photo = FSInputFile("photos/SuperDice.png")
    referral_code = None
    if len(message.text.split()) > 1:
        referral_code = message.text.split()[1].strip()
    
    user = await db.get_user(message.from_user.id)
    
    if not user:
        # Если есть реферальный код, находим реферера
        referred_by = None
        if referral_code:
            referrer = await db.get_user_by_referral_code(referral_code)
            if referrer:
                referred_by = referrer.id
        
        user = await db.create_user(
            message.from_user.id,
            message.from_user.username,
            message.from_user.first_name,
            message.from_user.last_name,
            referred_by
        )
        
        # Начисляем бонус рефереру
        if referred_by:
            await db.add_referral_earnings(referrer.user_id, 10)  # 25 звезд за реферала
            await bot.send_message(
                chat_id=referrer.user_id,
                text=f"🎉 Новый реферал!\n\n"
                     f"👤 {message.from_user.first_name} присоединился по вашей ссылке\n"
                     f"💎 Вам начислено 10 звезд\n"
                     f"📊 Всего рефералов: {referrer.referrals_count + 1}"
            )
        
        await message.answer_photo(
            path_to_photo,
            caption=
            f"""
            🎉 Добро пожаловать в SuperDice BOT!

Ваше приключение в мире азарта и больших выигрышей начинается прямо сейчас! Эти звезды — ваш первый шаг к покорению вершин. Используйте их, чтобы крутануть барабаны на самых горячих слотах и ощутить вкус победы!

Не упустите свой шанс! Забирайте звёзды и врывайтесь в игру! Удачи! 🚀
👇 Нажмите на кнопку ниже для начала игры""" +
            (f"\n🤝 Вы присоединились по реферальной ссылке!" if referral_code else ""),
            reply_markup=kb.main_menu()
        )
    else:
        await message.answer_photo(
            photo=path_to_photo,
            caption=f"""
            🎰 Добро пожаловать назад, чемпион!

🥰 Мы скучали по вашему настрою! Пока вас не было, выигрыш только росли, а новые игры ждали своего звёздного часа. Ваше возвращение — это знак для Фортуны! Готовы покорять новые вершины и сорвать большой куш? Удачи в играх! 
            
💎 Ваш баланс: {user.balance} звезд
👇 Нажмите на кнопку ниже для начала игры""",
            reply_markup=kb.main_menu()
        )

@dp.message(F.text == "⭐ Мой баланс")
async def show_balance(message: Message):
    user = await db.get_user(message.from_user.id)
    if user:
        await message.answer(f"💎 Ваш баланс: {user.balance} звезд")

@dp.message(F.text == "🎁 Ежедневный бонус")
async def daily_bonus_command(message: Message):
    user = await db.get_user(message.from_user.id)
    if not user:
        return
    
    # Проверяем, может ли пользователь получить бонус
    can_claim = await db.can_claim_daily_bonus(message.from_user.id)
    
    if can_claim:
        # Выдаем бонус
        new_balance = await db.claim_daily_bonus(message.from_user.id)
        
        if new_balance is not None:
            await message.answer(
                f"🎉 Поздравляем! Вы получили ежедневный бонус!\n\n"
                f"💎 Начислено: 5 звезд\n"
                f"📊 Новый баланс: {new_balance} звезд\n\n"
                f"Возвращайтесь завтра за новым бонусом! 🎁"
            )
        else:
            await message.answer("❌ Произошла ошибка при выдаче бонуса")
    else:
        # Показываем, сколько осталось ждать
        from datetime import datetime, timedelta
        now = datetime.utcnow()
        next_bonus_time = user.last_bonus_at + timedelta(hours=24)
        time_left = next_bonus_time - now
        
        hours_left = int(time_left.total_seconds() // 3600)
        minutes_left = int((time_left.total_seconds() % 3600) // 60)
        
        await message.answer(
            f"⏰ Вы уже получали бонус сегодня\n\n"
            f"Следующий бонус будет доступен через:\n"
            f"🕐 {hours_left} часов {minutes_left} минут\n\n"
            f"Возвращайтесь позже! 🎁"
        )

# Регистрируем обработчики платежей
from handlers.payment import pre_checkout_handler, success_payment_handler, pay_support_handler

dp.pre_checkout_query.register(pre_checkout_handler)
dp.message.register(success_payment_handler, F.successful_payment)
dp.message.register(pay_support_handler, Command("paysupport"))

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await db.init_db()
    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('exit')