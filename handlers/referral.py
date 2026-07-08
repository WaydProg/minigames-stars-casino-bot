from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from config import bot
from database import db
from keyboards import referral_menu, back_to_referral_menu, main_menu, back_to_main_menu
import asyncio

import database as datab

router = Router()

@router.message(F.text == "👥 Рефералы")
async def referral_command(message: Message):
    user = await db.get_user(message.from_user.id)
    if not user:
        return
    
    await message.answer(
        f"👥 Реферальная программа\n\n"
        f"💎 Зарабатывайте звезды за приглашенных друзей!\n\n"
        f"📊 Ваша статистика:\n"
        f"• Рефералов: {user.referrals_count}\n"
        f"• Заработано: {user.referral_earnings} звезд\n\n"
        f"🎯 За каждого приглашенного друга:\n"
        f"• Вы получаете: 10 звезд\n\n"
        f"Ваша реферальная ссылка:\n"
        f"https://t.me/dicelite_bot?start={user.referral_code}",
        reply_markup=referral_menu()
    )

@router.callback_query(F.data == "my_referrals")
async def show_my_referrals(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    if not user:
        await callback.answer("❌ Пользователь не найден")
        return
    
    referrals = await db.get_user_referrals(user.id)
    
    if not referrals:
        await callback.message.edit_text(
            "📊 У вас пока нет рефералов\n\n"
            "Приглашайте друзей и получайте бонусы!\n\n"
            "Ваша реферальная ссылка:\n"
            f"https://t.me/dicelite_bot?start={user.referral_code}",
            reply_markup=back_to_referral_menu()
        )
    else:
        referrals_text = "📊 Ваши рефералы:\n\n"
        for i, referral in enumerate(referrals, 1):
            referrals_text += f"{i}. {referral.first_name} (@{referral.username or 'нет'})\n"
            referrals_text += f"   📅 Зарегистрирован: {referral.registered_at.strftime('%d.%m.%Y')}\n"
            referrals_text += "   ─────────────────────\n"
        
        referrals_text += f"\n📈 Всего рефералов: {len(referrals)}"
        referrals_text += f"\n💎 Заработано: {user.referral_earnings} звезд"
        
        await callback.message.edit_text(
            referrals_text,
            reply_markup=back_to_referral_menu()
        )
    
    await callback.answer()

@router.callback_query(F.data == "referral_info")
async def show_referral_info(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    if not user:
        await callback.answer("❌ Пользователь не найден")
        return
    
    await callback.message.edit_text(
        f"💎 Реферальная программа\n\n"
        f"🎯 Как это работает:\n"
        f"1. Делитесь своей реферальной ссылкой с друзьями\n"
        f"2. Друг переходит по ссылке и запускает бота\n"
        f"3. Вы получаете 10 звезд!\n\n"
        f"💰 Условия:\n"
        f"• За каждого приглашенного друга: 10 звезд\n"
        f"• Нет ограничений на количество приглашений\n\n"
        f"📊 Ваша статистика:\n"
        f"• Рефералов: {user.referrals_count}\n"
        f"• Заработано: {user.referral_earnings} звезд\n\n"
        f"🎁 Бонус за активность:\n"
        f"Приведите 5 друзей - получите дополнительно 50 звезд! /bonus",
        reply_markup=back_to_referral_menu()
    )
    await callback.answer()

@router.callback_query(F.data == "copy_referral_link")
async def copy_referral_link(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    if not user:
        await callback.answer("❌ Пользователь не найден")
        return
    
    referral_link = f"https://t.me/dicelite_bot?start={user.referral_code}"
    
    await callback.message.edit_text(
        f"📋 Ваша реферальная ссылка:\n\n"
        f"`{referral_link}`\n\n"
        f"📝 Как использовать:\n"
        f"1. Скопируйте ссылку выше\n"
        f"2. Поделитесь с друзьями\n"
        f"3. Получайте бонусы за каждого приглашенного!\n\n"
        f"💡 Советы:\n"
        f"• Размещайте в социальных сетях\n"
        f"• Отправляйте в чатах и группах\n"
        f"• Делитесь с друзьями в личных сообщениях",
        parse_mode="Markdown",
        reply_markup=back_to_referral_menu()
    )
    await callback.answer()

@router.callback_query(F.data == "back_to_referral")
async def back_to_referral(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    if not user:
        await callback.answer("❌ Пользователь не найден")
        return
    
    await callback.message.edit_text(
        f"👥 Реферальная программа\n\n"
        f"💎 Зарабатывайте звезды за приглашенных друзей!\n\n"
        f"📊 Ваша статистика:\n"
        f"• Рефералов: {user.referrals_count}\n"
        f"• Заработано: {user.referral_earnings} звезд\n\n"
        f"🎯 За каждого приглашенного друга:\n"
        f"• Вы получаете: 25 звезд\n\n"
        f"Ваша реферальная ссылка:\n"
        f"https://t.me/dicelite_bot?start={user.referral_code}",
        reply_markup=referral_menu()
    )
    await callback.answer()

# @router.callback_query(F.data == "back_to_main")
# async def back_to_main_from_referral(callback: CallbackQuery):
#     await callback.message.edit_text(
#         "Главное меню:",
#         reply_markup=main_menu()
#     )
#     await callback.answer()

@router.message(Command("ref"))
async def ref_command(message: Message):
    user = await db.get_user(message.from_user.id)
    if not user:
        return
    
    referral_link = f"https://t.me/dicelite_bot?start={user.referral_code}"
    
    await message.answer(
        f"👥 Реферальная программа\n\n"
        f"Приглашайте друзей и получайте бонусы!\n\n"
        f"📊 Ваша статистика:\n"
        f"• Рефералов: {user.referrals_count}\n"
        f"• Заработано: {user.referral_earnings} звезд\n\n"
        f"🎯 За каждого друга: +50 звезд вам и другу\n\n"
        f"📋 Ваша ссылка:\n"
        f"`{referral_link}`\n\n"
        f"Поделитесь этой ссылкой с друзьями!",
        parse_mode="Markdown"
    )

# @router.message(Command("referrals"))
# async def referrals_stats_command(message: Message):
#     user = await db.get_user(message.from_user.id)
#     if not user:
#         return
    
#     referrals = await db.get_user_referrals(user.id)
    
#     if not referrals:
#         await message.answer(
#             "📊 У вас пока нет рефералов\n\n"
#             "Приглашайте друзей по ссылке:\n"
#             f"https://t.me/dicelite_bot?start={user.referral_code}\n\n"
#             "За каждого друга вы получите 50 звезд!"
#         )
#     else:
#         referrals_text = "📊 Ваши рефералы:\n\n"
#         for i, referral in enumerate(referrals, 1):
#             referrals_text += f"{i}. {referral.first_name} (@{referral.username or 'нет'})\n"
#             referrals_text += f"   📅 {referral.registered_at.strftime('%d.%m.%Y')}\n"
        
#         referrals_text += f"\n📈 Всего: {len(referrals)} рефералов"
#         referrals_text += f"\n💎 Заработано: {user.referral_earnings} звезд"
#         referrals_text += f"\n\n🎯 Приведите еще {5 - len(referrals)} друзей для бонуса 100 звезд!" if len(referrals) < 5 else "\n\n🎉 Вы получили бонус за 5+ рефералов!"
        
#         await message.answer(referrals_text)

# Бонус за 5 рефералов
@router.message(Command("bonus"))
async def check_referral_bonus(message: Message):
    user = await db.get_user(message.from_user.id)
    if not user:
        return
    
    if user.referrals_count >= 5 and user.referral_earnings < 50:
        # Начисляем бонус за 5 рефералов
        new_balance = await db.add_referral_earnings(user.user_id, 50)
        await message.answer(
            f"🎉 Поздравляем! Вы привели 5+ друзей!\n\n"
            f"💎 Вам начислен бонус: 50 звезд\n"
            f"📊 Новый баланс: {new_balance} звезд\n\n"
            f"🎯 Продолжайте приглашать друзей!"
        )
    elif user.referrals_count >= 5:
        await message.answer(
            f"🎉 Вы уже получили бонус за 5 рефералов!\n\n"
            f"📊 Рефералов: {user.referrals_count}\n"
            f"💎 Заработано: {user.referral_earnings} звезд\n\n"
            f"🎯 Приглашайте еще друзей!"
        )
    else:
        needed = 5 - user.referrals_count
        await message.answer(
            f"🎯 Приведите еще {needed} друзей для получения бонуса 50 звезд!\n\n"
            f"📊 Текущее количество: {user.referrals_count}/5\n"
            f"💎 Заработано: {user.referral_earnings} звезд\n\n"
            f"Ваша ссылка:\n"
            f"https://t.me/dicelite_bot?start={user.referral_code}"
        )