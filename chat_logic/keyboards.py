from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from database import db

async def start_game(invited, game_id):
    builder = InlineKeyboardBuilder()

    builder.add(InlineKeyboardButton(text='✅ Принять игру', callback_data=f'gamechat_start_{invited}_{game_id}', style='SUCCESS'))
    builder.add(InlineKeyboardButton(text='❌ Отклонить игру', callback_data=f'gamechat_rejected_{invited}_{game_id}', style='DANGER'))

    return builder.adjust(2).as_markup()