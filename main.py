from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from config import dp, bot
from database import db
import keyboards as kb
from game_handlers import router as game_dp
from admin_panel import router as admin_dp
from payment_handlers import router as payment_dp
import asyncio
import logging
from handlers.referral import router as referral_dp
from handlers.cryptobot_handler import router as cryptobot_dp
from chat_logic.handlers import router as chat_dp
from aiogram.types import FSInputFile
from shedulers import scheduler
from aiogram.fsm.context import FSMContext
from payment_handlers import deposit_command
from aiogram.methods import GetAvailableGifts, SendGift
import states as states


# Регистрируем роутеры
dp.include_router(chat_dp)
dp.include_router(game_dp)
dp.include_router(admin_dp)
dp.include_router(payment_dp)
dp.include_router(referral_dp)
dp.include_router(cryptobot_dp)

main_photo = FSInputFile("photos/main.png")
balance_photo = FSInputFile("photos/balance.png")
games_photo = FSInputFile("photos/games.png")
referals_photo = FSInputFile("photos/referals.png")

@dp.message(CommandStart())
async def start_command(message: Message, state:FSMContext, command: CommandStart):
    await state.clear()

    args = command.args
    user = await db.get_user(message.from_user.id)

    if args == "deposit" and user:
        await deposit_command(message)
    else:

        referral_code = None
        if len(message.text.split()) > 1:
            referral_code = message.text.split()[1].strip()
        
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
                main_photo,
                caption=
                f"""🎉 Добро пожаловать в SuperDice BOT!
    
Ваш путь к вершинам начинается здесь и сейчас! Эти звёзды — ваш пропуск в мир игр. Тратьте их на подарки и наслаждайтесь каждой победой!
    
Не упустите свой шанс! Забирайте звёзды и врывайтесь в игру! Удачи! 🚀
👇 Нажмите на кнопку ниже для начала игры""" +
(f"\n🤝 Вы присоединились по реферальной ссылке!" if referral_code else ""),
                reply_markup=kb.main_menu()
            )
        else:

            if user.banned:
                await message.answer('❌ Доступ запрещен, вы забанены в данном боте')
                return

            await message.answer_photo(
                photo=main_photo,
                caption=f"""🎰 Добро пожаловать назад, чемпион!
    
🥰 Мы скучали по вашему настрою! Пока вас не было, бонусы множились, а новые испытания ждали своего звёздного часа. Ваше возвращение — это знак удачи! Готовы покорять новые вершины и забирать главные призы? Удачи в играх!
                
💎 Ваш баланс: {user.balance} звезд
👇 Нажмите на кнопку ниже для начала игры""",
                reply_markup=kb.main_menu()
            )

@dp.message(F.text == "⭐ Мой баланс")
async def show_balance(message: Message):
    user = await db.get_user(message.from_user.id)

    if user.banned:
        await message.answer('❌ Доступ запрещен, вы забанены в данном боте')
        return
    
    if user:
        await message.answer_photo(balance_photo, caption=f"💎 Ваш баланс: {user.balance} звезд")

@dp.message(F.text == "🎁 Ежедневный бонус")
async def daily_bonus_command(message: Message):
    user = await db.get_user(message.from_user.id)

    if user.banned:
        await message.answer('❌ Доступ запрещен, вы забанены в данном боте')
        return
    
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

@dp.message(F.text == '🎉 Ввести промокод')
async def activate_promocode(message:Message, state:FSMContext):
    user = await db.get_user(message.from_user.id)

    if user.banned:
        await message.answer('❌ Доступ запрещен, вы забанены в данном боте')
        return
    
    await message.answer('👇 Введите свой промокод', reply_markup=kb.back())

    await state.set_state(states.ActivatePromocode.code)

@dp.message(states.ActivatePromocode.code, F.text)
async def process_activate_promocode(message:Message, state:FSMContext):
    user = await db.get_user(message.from_user.id)
    
    if user.banned:
        await message.answer('❌ Доступ запрещен, вы забанены в данном боте')
        return
    
    code = message.text
    promo = await db.get_promocode_by_code(code)

    if promo and promo.is_available == 1:
        try:
            await db.add_use_promo(message.from_user.id, promo.id)
            balance = await db.update_balance(message.from_user.id, promo.reward, 'promocode', f'activate promocode {code}')

            await message.answer(f'🎉 Промокод {code} успешно активирован! \n⭐ Ваш новый баланс - {balance}⭐')

            await state.clear()
        except ValueError as e:
            await message.answer(f'{e}')
    else:
        await message.answer('❌ Промокод не найден или отключен, попробуйте другой')

@dp.message(F.text == '📩 Купить подарок')
async def send_gift_username(message:Message, state:FSMContext):
    user = await db.get_user(message.from_user.id)
    
    if user.banned:
        await message.answer('❌ Доступ запрещен, вы забанены в данном боте')
        return
    
    await message.answer('👇 Введите @username пользователя', reply_markup=kb.back())

    await state.set_state(states.SendGift.username)

@dp.message(states.SendGift.username, F.text)
async def send_gift_text(message:Message, state:FSMContext):
    user = await db.get_user(message.from_user.id)
    
    if user.banned:
        await message.answer('❌ Доступ запрещен, вы забанены в данном боте')
        return

    await state.update_data(username=message.text[1:])

    await message.answer('👇 Введите комментарий к подарку (или "-")', reply_markup=kb.back())

    await state.set_state(states.SendGift.msg)

@dp.message(states.SendGift.msg, F.text)
async def proces_send_gift(message:Message, state:FSMContext):
    user = await db.get_user(message.from_user.id)
    
    if user.banned:
        await message.answer('❌ Доступ запрещен, вы забанены в данном боте')
        return
    
    await state.update_data(msg = (message.text if message.text != '-' else None))
    gifts = await bot(GetAvailableGifts())

    await message.answer('👇 Выберите подарок для отправки', reply_markup= await kb.list_avaible_gifts(gifts.gifts))

@dp.callback_query(F.data.startswith('usergift_'))
async def send_gift_from_user(callback:CallbackQuery, state:FSMContext):
    user = await db.get_user(callback.from_user.id)

    if user.banned:
        await callback.answer()
        await callback.answer('❌ Доступ запрещен, вы забанены в данном боте')
        return
    
    gift_id = callback.data.split('_')[1]
    gift_star_count = callback.data.split('_')[2]

    await callback.answer()

    if int(user.balance) < int(gift_star_count):
        await callback.message.answer('❌ Недостаточно звезд на балансе')
        return

    data = await state.get_data()
    username = data.get('username')
    msg = data.get('msg')

    user_id = await db.get_user_by_username(username)

    try:

        await bot.send_gift(
            user_id=int(user_id.user_id),
            gift_id=str(gift_id),  
            text=msg
        )

        await callback.message.answer(f'✅ Подарок успешно отправлен пользователю: @{username}')

    except Exception as e:
        await callback.message.answer(f'❌ Ошибка отправки подарка: {e}')

@dp.message(F.text == '📤 Отправить звезды')
async def send_stars(message:Message, state:FSMContext):
    user = await db.get_user(message.from_user.id)

    if user.banned:
        await message.answer('❌ Доступ запрещен, вы забанены в данном боте')
        return

    await message.answer('👇 Введите @username пользователя', reply_markup=kb.back())

    await state.set_state(states.SendStars.username)

@dp.message(states.SendStars.username, F.text)
async def send_stars_text(message:Message, state:FSMContext):
    user = await db.get_user(message.from_user.id)

    if user.banned:
        await message.answer('❌ Доступ запрещен, вы забанены в данном боте')
        return
    
    await state.update_data(username=message.text[1:])

    await message.answer('👇 Введите комментарий к переводу (или "-")', reply_markup=kb.back())

    await state.set_state(states.SendStars.msg)

@dp.message(states.SendStars.msg, F.text)
async def send_stars_count(message:Message, state:FSMContext):
    user = await db.get_user(message.from_user.id)

    if user.banned:
        await message.answer('❌ Доступ запрещен, вы забанены в данном боте')
        return
    
    await state.update_data(msg = (message.text if message.text != '-' else None))

    await message.answer('👇 Введите кол-во звезд', reply_markup=kb.back())

    await state.set_state(states.SendStars.count)

@dp.message(states.SendStars.count, F.text)
async def proces_send_stars(message:Message, state:FSMContext):
    user = await db.get_user(message.from_user.id)

    if user.banned:
        await message.answer('❌ Доступ запрещен, вы забанены в данном боте')
        return
    
    if int(user.balance) < int(message.text):
        await message.answer('❌ Недостаточно звезд на балансе')
        return

    data = await state.get_data()
    description = data.get('msg')
    user2 = await db.get_user_by_username(data.get('username'))
    user_id = user.user_id
    user2_id = user2.user_id

    try:
        await db.add_stars_to_user_by_userid(
            user_id,
            int(f'-{message.text}'),
            'transaction',
            f'Перевод звезд пользователю @{data.get('username')}'
        )

        await db.add_stars_to_user_by_userid(
            user2_id,
            int(message.text),
            'transaction',
            f'Перевод звезд от пользователя @{data.get('username')}'
        )

        text = f"""📩 Получен перевод от пользователя @{user.username}

💵 Перевод на сумму: {message.text}⭐
"""
        text += f'📋 Комментарий: \n{description}' if description else ''


        await bot.send_message(chat_id=user2_id, text=text)
        await message.answer(f'✅ Перевод пользователю @{data.get('username')} отправлен успешно')

    except ValueError as e:
        await message.answer(f'❌ Ошибка перевода: {e}') 


# Регистрируем обработчики платежей
from handlers.payment import pre_checkout_handler, success_payment_handler, pay_support_handler

dp.pre_checkout_query.register(pre_checkout_handler)
dp.message.register(success_payment_handler, F.successful_payment)
dp.message.register(pay_support_handler, Command("paysupport"))

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await db.init_db()
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('exit')