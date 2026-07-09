from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.enums import ButtonStyle
from database import db

def main_menu():
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="🎰 Игры", style=ButtonStyle.SUCCESS))
    builder.add(KeyboardButton(text="⭐ Мой баланс", style=ButtonStyle.PRIMARY))
    builder.add(KeyboardButton(text="💫 Пополнить", style=ButtonStyle.PRIMARY))
    builder.add(KeyboardButton(text="🎉 Ввести промокод", style=ButtonStyle.DANGER))
    builder.add(KeyboardButton(text="🎁 Ежедневный бонус", style=ButtonStyle.DANGER))
    builder.add(KeyboardButton(text="💰 Вывод"))
    builder.add(KeyboardButton(text="👥 Рефералы")) 
    builder.add(KeyboardButton(text="📊 Статистика"))
    builder.add(KeyboardButton(text="ℹ️ Помощь"))
    builder.adjust(1, 2)
    return builder.as_markup(resize_keyboard=True)

def back():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text='◀️ Назад', callback_data="back_to_games_list"))
    builder.adjust(1)
    return builder.as_markup()


def deposit_menu():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="⭐ 1 звезда - 1⭐", callback_data="deposit_1"))
    builder.add(InlineKeyboardButton(text="⭐ 25 звезд - 25⭐", callback_data="deposit_25"))
    builder.add(InlineKeyboardButton(text="⭐ 50 звезд - 50⭐", callback_data="deposit_50"))
    builder.add(InlineKeyboardButton(text="⭐ 100 звезд - 100⭐", callback_data="deposit_100"))
    builder.add(InlineKeyboardButton(text="⭐ 200 звезд - 200⭐", callback_data="deposit_200"))
    builder.add(InlineKeyboardButton(text="⭐ 500 звезд - 500⭐", callback_data="deposit_500"))
    builder.add(InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main"))
    builder.adjust(1)
    return builder.as_markup()

def cancel_keyboard():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="❌ Отмена", callback_data='cancel_keyboard'))
    return builder.as_markup()

def withdrawal_approve_keyboard(request_id: int):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="✅ Выполнено",
        callback_data=f"approve_withdraw_{request_id}"
    ))
    builder.add(InlineKeyboardButton(
        text="❌ Отклонить",
        callback_data=f"reject_withdraw_{request_id}"
    ))
    return builder.as_markup()

def admin_menu():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="⚙️ Настройки игр", callback_data="admin_settings"))
    builder.add(InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats"))
    builder.add(InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users"))
    builder.add(InlineKeyboardButton(text="💎 Добавить звезды", callback_data="admin_add_stars"))
    builder.add(InlineKeyboardButton(text="🎉 Добавить промокод", callback_data="admin_add_promocode"))
    builder.add(InlineKeyboardButton(text="📋 Список промокодов", callback_data="admin_promocodes"))
    builder.adjust(2)
    return builder.as_markup()

def game_settings_menu():
    builder = InlineKeyboardBuilder()
    games = ['dice', 'dart', 'basketball', 'football', 'bowling', 'slot']
    for game in games:
        builder.add(InlineKeyboardButton(
            text=f"⚙️ {game.capitalize()}", 
            callback_data=f"setting_{game}"
        ))
    builder.add(InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back"))
    builder.adjust(2)
    return builder.as_markup()

def back_to_admin():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back"))
    return builder.as_markup()

def back_to_game_menu(game_type: str):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🎰 Сыграть еще раз", callback_data=f"game_{game_type}"))
    builder.add(InlineKeyboardButton(text='◀️ Выбор игры', callback_data='back_to_games_list'))
    return builder.adjust(1).as_markup()

def back_to_main_menu():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="◀️ В главное меню", callback_data="back_to_main"))
    return builder.as_markup()

def withdrawals_menu():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="📋 Активные заявки", callback_data="withdrawals_active"))
    builder.add(InlineKeyboardButton(text="📊 История выводов", callback_data="withdrawals_history"))
    builder.add(InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back"))
    builder.adjust(1)
    return builder.as_markup()

def games_menu():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🎲 Кубик", callback_data="game_dice"))
    builder.add(InlineKeyboardButton(text="🎯 Дартс", callback_data="game_dart"))
    builder.add(InlineKeyboardButton(text="🏀 Баскетбол", callback_data="game_basketball"))
    builder.add(InlineKeyboardButton(text="⚽ Футбол", callback_data="game_football"))
    builder.add(InlineKeyboardButton(text="🎳 Боулинг", callback_data="game_bowling"))
    builder.add(InlineKeyboardButton(text="🎰 Рулетка", callback_data="game_slot"))
    builder.adjust(2)
    return builder.as_markup()

def game_action_menu(game_type: str):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🎮 Играть", callback_data=f"play_{game_type}"))
    builder.add(InlineKeyboardButton(text="💰 Изменить ставку", callback_data=f"bet_{game_type}"))
    builder.add(InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_games_list"))
    builder.adjust(1)
    return builder.as_markup()

def referral_menu():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="📊 Мои рефералы", callback_data="my_referrals"))
    builder.add(InlineKeyboardButton(text="💎 Реферальная программа", callback_data="referral_info"))
    builder.add(InlineKeyboardButton(text="📋 Скопировать ссылку", callback_data="copy_referral_link"))
    builder.adjust(1)
    return builder.as_markup()

def back_to_referral_menu():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_referral"))
    return builder.as_markup()

def payment_methods_menu():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="⭐ Telegram Stars", callback_data="pay_method_stars"))
    builder.add(InlineKeyboardButton(text="💎 Cryptobot (TON)", callback_data="pay_method_cryptobot"))
    builder.adjust(1)
    return builder.as_markup()

def cryptobot_packages_menu():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="💎 25 звезд - 0.125 TON", callback_data="crypto_25"))
    builder.add(InlineKeyboardButton(text="💎 50 звезд - 0.25 TON", callback_data="crypto_50"))
    builder.add(InlineKeyboardButton(text="💎 100 звезд - 0.5 TON", callback_data="crypto_100"))
    builder.add(InlineKeyboardButton(text="💎 200 звезд - 1 TON", callback_data="crypto_200"))
    builder.add(InlineKeyboardButton(text="💎 500 звезд - 2 TON", callback_data="crypto_500"))
    builder.add(InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_payment_method"))
    builder.adjust(1)
    return builder.as_markup()

def cryptobot_payment_keyboard(invoice_url: str):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="💳 Оплатить в CryptoBot", url=invoice_url))
    builder.add(InlineKeyboardButton(text="✅ Проверить оплату", callback_data="check_crypto_payment"))
    builder.add(InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_crypto_payment"))
    builder.adjust(1)
    return builder.as_markup()

def approve_or_cancel():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text='✅ Подтвердить создание', callback_data='promo_approve'))
    builder.add(InlineKeyboardButton(text='❌ Отменить создание', callback_data='promo_cancel'))
    builder.adjust(2)
    return builder.as_markup()

async def show_all_promocodes():
    builder = InlineKeyboardBuilder()
    promocodes = await db.get_promocodes()

    promocodes_sorted = sorted(promocodes, key=lambda p: p.is_available, reverse=True)

    for promo in promocodes_sorted:
        builder.add(
            InlineKeyboardButton(
                text=f'{'✅' if promo.is_available else '❌'} {promo.name} | {promo.code}', 
                callback_data=f'code_{promo.code}'
                ))
    
    builder.adjust(1)
    return builder.as_markup()

async def code_actions(promo_id, is_available):
    builder = InlineKeyboardBuilder()

    builder.add(InlineKeyboardButton(text='❌ Отключить', callback_data=f'action_off_{promo_id}')) if is_available else None
    builder.add(InlineKeyboardButton(text='🗑️ Удалить', callback_data=f'action_delete_{promo_id}'))
    builder.add(InlineKeyboardButton(text='◀️ Назад', callback_data='admin_back'))

    builder.adjust(1)
    return builder.as_markup()