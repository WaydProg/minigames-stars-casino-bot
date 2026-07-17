from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, PreCheckoutQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import bot, WITHDRAWAL_CHAT_ID
from aiogram.types import FSInputFile
from database import db
from handlers.payment import send_invoice_handler
import asyncio
from datetime import datetime

import keyboards as kb

router = Router()

class WithdrawalState(StatesGroup):
    waiting_for_amount = State()

# Пакеты пополнения
DEPOSIT_PACKAGES = {
    "1": 1,
    "25": 25,
    "50": 50,
    "100": 100,
    "200": 200,
    "500": 500
}

deposit_photo = FSInputFile("photos/DEPOSIT.png")

@router.message(F.text == "💫 Пополнить")
async def deposit_command(message: Message):
    user = await db.get_user(message.from_user.id)

    if user.banned:
        await message.answer('❌ Доступ запрещен, вы забанены в данном боте')
        return
    
    await message.answer_photo(deposit_photo,
        caption="💫 Выберите способ пополнения:",
        reply_markup=kb.payment_methods_menu()
    )

@router.callback_query(F.data.startswith("deposit_"))
async def process_deposit(callback: CallbackQuery):
    package = callback.data.split("_")[1]
    
    if package not in DEPOSIT_PACKAGES:
        await callback.answer("❌ Неверный пакет")
        return
    
    amount = DEPOSIT_PACKAGES[package]
    await send_invoice_handler(callback.message, amount)
    await callback.answer()

@router.pre_checkout_query()
async def process_pre_checkout(query: PreCheckoutQuery):
    await query.answer(ok=True)

@router.message(F.successful_payment)
async def process_successful_payment(message: Message):
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

@router.message(Command("paysupport"))
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

@router.message(F.text == "💰 Вывод")
async def withdraw_command(message: Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)
    if not user:
        return
    
    await message.answer(
        f"💰 Вывод средств\n\n"
        f"💎 Ваш баланс: {user.balance} звезд\n"
        f"‼️ Вывод возможет от 100 звезд\n"
        f"📝 Введите количество звезд для вывода:",
        reply_markup=kb.cancel_keyboard()
    )
    await state.set_state(WithdrawalState.waiting_for_amount)

@router.callback_query(StateFilter(WithdrawalState.waiting_for_amount), F.data == "cancel_keyboard")
async def cancel_withdrawal(callback:CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    await callback.message.answer("❌ Вывод отменен", reply_markup=kb.main_menu())

@router.message(WithdrawalState.waiting_for_amount)
async def process_withdrawal_amount(message: Message, state: FSMContext):
    try:
        amount = int(message.text)
        user = await db.get_user(message.from_user.id)
        
        if not user:
            await message.answer("❌ Пользователь не найден")
            await state.clear()
            return
        
        if amount < 100:
            await message.answer("❌ Минимальная сумма вывода: 100 звезд")
            return
        
        if amount > user.balance:
            await message.answer("❌ Недостаточно средств на балансе")
            return
        
        # Создаем заявку на вывод
        withdrawal = await db.create_withdrawal_request(message.from_user.id, amount)
        
        if not withdrawal:
            await message.answer("❌ Ошибка при создании заявки")
            await state.clear()
            return
        
        # Отправляем заявку в чат вывода
        request_text = f"""
💰 <b>ЗАЯВКА НА ВЫВОД</b>

👤 <b>Пользователь:</b> {user.first_name} (@{user.username or 'нет'})
🆔 <b>ID:</b> {user.user_id}
💎 <b>Сумма:</b> {amount} звезд
📊 <b>Баланс:</b> {user.balance} звезд
⏰ <b>Время:</b> {datetime.now().strftime('%H:%M:%S')}

#вывод #{user.user_id}
"""
        sent_message = await bot.send_message(
            chat_id=WITHDRAWAL_CHAT_ID,
            text=request_text,
            parse_mode="HTML",
            reply_markup=kb.withdrawal_approve_keyboard(withdrawal.id)
        )
        
        # Сохраняем ID сообщения
        await db.update_withdrawal_request(withdrawal.id, 'pending', sent_message.message_id)
        
        await message.answer(
            f"✅ Заявка на вывод {amount} звезд создана!\n\n"
            f"Ожидайте обработки администратором.",
            reply_markup=kb.main_menu()
        )
        
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Пожалуйста, введите число")
    except Exception as e:
        print(f"Ошибка при создании заявки на вывод: {e}")
        await message.answer("❌ Произошла ошибка при создании заявки")
        await state.clear()

@router.callback_query(F.data.startswith("approve_withdraw_"))
async def approve_withdrawal(callback: CallbackQuery):
    try:
        request_id = int(callback.data.replace("approve_withdraw_", ""))
        withdrawal = await db.get_withdrawal_request(request_id)
        
        if not withdrawal:
            await callback.answer("❌ Заявка не найдена")
            return
        
        if withdrawal.status != 'pending':
            await callback.answer("❌ Заявка уже обработана")
            return
        
        # Получаем пользователя через связь
        user = withdrawal.user
        if not user:
            await callback.answer("❌ Пользователь не найден")
            return
        
        # Обновляем баланс
        new_balance = await db.update_balance(
            user.user_id,  # Используем user_id из объекта User
            -withdrawal.amount, 
            "withdraw", 
            f"Вывод {withdrawal.amount} звезд"
        )
        
        if new_balance is None:
            await callback.answer("❌ Ошибка при обновлении баланса")
            return
        
        # Обновляем статус заявки
        await db.update_withdrawal_request(request_id, 'approved')
        
        # Уведомляем пользователя
        await bot.send_message(
            chat_id=user.user_id,
            text=f"✅ Вывод выполнен!\n\n"
                 f"💎 Сумма: {withdrawal.amount} звезд\n"
                 f"📊 Новый баланс: {new_balance} звезд"
        )
        
        # Обновляем сообщение в чате
        await callback.message.edit_text(
            f"✅ <b>ВЫПОЛНЕНО</b>\n\n"
            f"👤 Пользователь: {user.first_name}\n"
            f"💎 Сумма: {withdrawal.amount} звезд\n"
            f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}",
            parse_mode="HTML"
        )
        
        await callback.answer("✅ Вывод выполнен")
        
    except Exception as e:
        print(f"Ошибка при обработке вывода: {e}")
        await callback.answer("❌ Произошла ошибка")

@router.callback_query(F.data.startswith("reject_withdraw_"))
async def reject_withdrawal(callback: CallbackQuery):
    try:
        request_id = int(callback.data.replace("reject_withdraw_", ""))
        withdrawal = await db.get_withdrawal_request(request_id)
        
        if not withdrawal:
            await callback.answer("❌ Заявка не найдена")
            return
        
        if withdrawal.status != 'pending':
            await callback.answer("❌ Заявка уже обработана")
            return
        
        # Получаем пользователя через связь
        user = withdrawal.user
        if not user:
            await callback.answer("❌ Пользователь не найден")
            return
        
        # Обновляем статус заявки
        await db.update_withdrawal_request(request_id, 'rejected')
        
        # Уведомляем пользователя
        await bot.send_message(
            chat_id=user.user_id,
            text=f"❌ Вывод отклонен\n\n"
                 f"💎 Сумма: {withdrawal.amount} звезд\n"
                 f"📊 Ваш баланс: {user.balance} звезд\n\n"
                 f"По вопросам обращайтесь к администратору."
        )
        
        # Обновляем сообщение в чате
        await callback.message.edit_text(
            f"❌ <b>ОТКЛОНЕНО</b>\n\n"
            f"👤 Пользователь: {user.first_name}\n"
            f"💎 Сумма: {withdrawal.amount} звезд\n"
            f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}",
            parse_mode="HTML"
        )
        
        await callback.answer("❌ Вывод отклонен")
        
    except Exception as e:
        print(f"Ошибка при отклонении вывода: {e}")
        await callback.answer("❌ Произошла ошибка")

@router.callback_query(F.data == "pay_method_stars")
async def select_stars_method(callback: CallbackQuery):
    await callback.message.edit_caption(caption=
        "⭐ Пополнение через Telegram Stars\n\n"
        "Выберите пакет пополнения:",
        reply_markup=kb.deposit_menu()
    )
    await callback.answer()

@router.callback_query(F.data == "back_to_payment_method")
async def back_to_payment_method(callback: CallbackQuery):
    await callback.message.edit_caption(
        caption="💫 Выберите способ пополнения:",
        reply_markup=kb.payment_methods_menu()
    )
    await callback.answer()

@router.callback_query(F.data == "back_to_main")
async def back_to_main_from_referral(callback: CallbackQuery):
    await callback.message.edit_caption(caption=
        "Главное меню:",
        reply_markup=kb.payment_methods_menu()
    )
    await callback.answer()