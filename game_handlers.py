from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import bot, HISTORY_CHAT_ID, ADMIN_IDS
from database import db
import random
import asyncio
from datetime import datetime
from aiogram.types import FSInputFile

import keyboards as kb

router = Router()

# Состояния для FSM
class BetState(StatesGroup):
    waiting_for_bet = State()

# Названия игр для отображения
GAME_NAMES = {
    "dice": "🎲 Игра в кубик",
    "dart": "🎯 Игра в дартс", 
    "basketball": "🏀 Баскетбол",
    "football": "⚽ Футбол",
    "bowling": "🎳 Боулинг",
    "slot": "🎰 Рулетка"
}

# Эмодзи для игр
GAME_EMOJIS = {
    "dice": "🎲",
    "dart": "🎯",
    "basketball": "🏀",
    "football": "⚽",
    "bowling": "🎳",
    "slot": "🎰"
}

# Условия победы для каждой игры
WIN_CONDITIONS = {
    "dice": "Выпадает 5 или 6 на кубике",
    "dart": "Попадание в цель (значение 5 или 6)",
    "basketball": "Попадание в корзину (значение 4, 5 или 6)", 
    "football": "Гол! (значение 4 или 5)",
    "bowling": "Страйк! (значение 5 или 6)",
    "slot": "Выигрыш определяется случайным образом\n🎰 Джекпот при значении 1 (5x множитель)"
}

# Победные значения для каждой игры
WIN_VALUES = {
    "dice": [5, 6],           # Кубик: 5-6 для победы
    "dart": [5, 6],           # Дартс: 5-6 для победы  
    "basketball": [4, 5, 6],  # Баскетбол: 4-6 для победы
    "football": [4, 5],       # Футбол: 4-5 для победы
    "bowling": [5, 6],        # Боулинг: 5-6 для победы
    "slot": []                # Рулетка: особая логика
}

photo = FSInputFile('photos/SuperDice.png')

async def send_game_history(user_id: int, username: str, first_name: str, game_type: str, 
                           bet_amount: int, win_amount: int, dice_value: int = None):
    """Отправляет историю игры в отдельный чат"""
    try:
        if HISTORY_CHAT_ID:
            game_emoji = GAME_EMOJIS.get(game_type, "🎮")
            result_emoji = "🎉" if win_amount > 0 else "😢"
            result_text = "ВЫИГРЫШ" if win_amount > 0 else "ПРОИГРЫШ"
            
            history_message = f"""
{game_emoji} <b>ИГРА ЗАВЕРШЕНА</b> {game_emoji}

👤 <b>Игрок:</b> {first_name} (@{username if username else 'нет username'})
🆔 <b>ID:</b> {user_id}
🎮 <b>Игра:</b> {GAME_NAMES[game_type]}
💰 <b>Ставка:</b> {bet_amount} звезд

🎯 <b>Результат:</b> {result_emoji} {result_text}
"""
            
            if dice_value is not None:
                history_message += f"🎲 <b>Выпало:</b> {dice_value}\n"
            
            if win_amount > 0:
                history_message += f"🏆 <b>Выигрыш:</b> {win_amount} звезд\n"
                history_message += f"📈 <b>Множитель:</b> x{win_amount / bet_amount:.1f}\n"
            
            history_message += f"⏰ <b>Время:</b> {datetime.now().strftime('%H:%M:%S')}"
            
            await bot.send_message(
                chat_id=HISTORY_CHAT_ID,
                text=history_message,
                parse_mode="HTML"
            )
    except Exception as e:
        print(f"Ошибка при отправке истории в чат: {e}")

async def play_dice(callback: CallbackQuery, setting, bet_amount: int):
    message = await callback.message.answer_dice(emoji="🎲")
    dice_value = message.dice.value
    
    # Получаем текущий баланс пользователя
    user = await db.get_user(callback.from_user.id)
    
    # Проверяем выигрыш по значению кубика
    if dice_value in WIN_VALUES["dice"] and random.random() < setting.win_chance:
        win_amount = int(bet_amount * setting.win_multiplier)
        new_balance = await db.update_balance(
            callback.from_user.id, win_amount, "win", f"Выигрыш в dice (выпало {dice_value})"
        )
        await db.update_game_stat(
            callback.from_user.id, "dice", bet_amount, win_amount
        )
        
        # Отправляем историю в чат
        await send_game_history(
            callback.from_user.id,
            callback.from_user.username,
            callback.from_user.first_name,
            "dice",
            bet_amount,
            win_amount,
            dice_value
        )
        
        await callback.message.answer(
            f"🎲 Выпало: {dice_value}\n🎉 Поздравляем! Вы выиграли {win_amount} звезд!\n"
            f"💎 Ваш баланс: {new_balance} звезд"
        )
    else:
        await db.update_game_stat(callback.from_user.id, "dice", bet_amount, 0)
        
        # Отправляем историю в чат
        await send_game_history(
            callback.from_user.id,
            callback.from_user.username,
            callback.from_user.first_name,
            "dice",
            bet_amount,
            0,
            dice_value
        )
        
        await callback.message.answer(
            f"🎲 Выпало: {dice_value}\n😢 К сожалению вы проиграли в этот раз, попробуйте еще, вдруг повезет\n"
            f"💎 Ваш баланс: {user.balance} звезд"
        )

async def play_dart(callback: CallbackQuery, setting, bet_amount: int):
    message = await callback.message.answer_dice(emoji="🎯")
    dart_value = message.dice.value
    
    # Получаем текущий баланс пользователя
    user = await db.get_user(callback.from_user.id)
    
    # Проверяем попадание в цель (5-6 для победы)
    if dart_value in WIN_VALUES["dart"] and random.random() < setting.win_chance:
        win_amount = int(bet_amount * setting.win_multiplier)
        new_balance = await db.update_balance(
            callback.from_user.id, win_amount, "win", f"Выигрыш в dart (выпало {dart_value})"
        )
        await db.update_game_stat(
            callback.from_user.id, "dart", bet_amount, win_amount
        )
        
        # Отправляем историю в чат
        await send_game_history(
            callback.from_user.id,
            callback.from_user.username,
            callback.from_user.first_name,
            "dart",
            bet_amount,
            win_amount,
            dart_value
        )
        
        await callback.message.answer(
            f"🎯 Выпало: {dart_value}\n🎯 Отличный бросок! Попадание в цель! Вы выиграли {win_amount} звезд!\n"
            f"💎 Ваш баланс: {new_balance} звезд"
        )
    else:
        await db.update_game_stat(callback.from_user.id, "dart", bet_amount, 0)
        
        # Отправляем историю в чат
        await send_game_history(
            callback.from_user.id,
            callback.from_user.username,
            callback.from_user.first_name,
            "dart",
            bet_amount,
            0,
            dart_value
        )
        
        await callback.message.answer(
            f"🎯 Выпало: {dart_value}\n💨 Промах! Попробуйте еще раз\n"
            f"💎 Ваш баланс: {user.balance - bet_amount} звезд"
        )

async def play_basketball(callback: CallbackQuery, setting, bet_amount: int):
    message = await callback.message.answer_dice(emoji="🏀")
    basketball_value = message.dice.value
    
    # Получаем текущий баланс пользователя
    user = await db.get_user(callback.from_user.id)
    
    # Проверяем попадание в корзину (4-6 для победы)
    if basketball_value in WIN_VALUES["basketball"] and random.random() < setting.win_chance:
        win_amount = int(bet_amount * setting.win_multiplier)
        new_balance = await db.update_balance(
            callback.from_user.id, win_amount, "win", f"Выигрыш в basketball (выпало {basketball_value})"
        )
        await db.update_game_stat(
            callback.from_user.id, "basketball", bet_amount, win_amount
        )
        
        # Отправляем историю в чат
        await send_game_history(
            callback.from_user.id,
            callback.from_user.username,
            callback.from_user.first_name,
            "basketball",
            bet_amount,
            win_amount,
            basketball_value
        )
        
        await callback.message.answer(
            f"🏀 Выпало: {basketball_value}\n🏀 Отличный бросок! Мяч в корзине! Вы выиграли {win_amount} звезд!\n"
            f"💎 Ваш баланс: {new_balance} звезд"
        )
    else:
        await db.update_game_stat(callback.from_user.id, "basketball", bet_amount, 0)
        
        # Отправляем историю в чат
        await send_game_history(
            callback.from_user.id,
            callback.from_user.username,
            callback.from_user.first_name,
            "basketball",
            bet_amount,
            0,
            basketball_value
        )
        
        await callback.message.answer(
            f"🏀 Выпало: {basketball_value - 1}\n❌ Мисс! Мяч не попал в корзину. Попробуйте еще раз\n"
            f"💎 Ваш баланс: {user.balance - bet_amount} звезд"
        )

async def play_football(callback: CallbackQuery, setting, bet_amount: int):
    message = await callback.message.answer_dice(emoji="⚽")
    football_value = message.dice.value
    
    # Получаем текущий баланс пользователя
    user = await db.get_user(callback.from_user.id)
    
    # Проверяем гол (4-5 для победы)
    if football_value in WIN_VALUES["football"] and random.random() < setting.win_chance:
        win_amount = int(bet_amount * setting.win_multiplier)
        new_balance = await db.update_balance(
            callback.from_user.id, win_amount, "win", f"Выигрыш в football (выпало {football_value})"
        )
        await db.update_game_stat(
            callback.from_user.id, "football", bet_amount, win_amount
        )
        
        # Отправляем историю в чат
        await send_game_history(
            callback.from_user.id,
            callback.from_user.username,
            callback.from_user.first_name,
            "football",
            bet_amount,
            win_amount,
            football_value
        )
        
        await callback.message.answer(
            f"⚽ Выпало: {football_value}\n⚽ Гол! Отличный удар! Вы выиграли {win_amount} звезд!\n"
            f"💎 Ваш баланс: {new_balance} звезд"
        )
    else:
        await db.update_game_stat(callback.from_user.id, "football", bet_amount, 0)
        
        # Отправляем историю в чат
        await send_game_history(
            callback.from_user.id,
            callback.from_user.username,
            callback.from_user.first_name,
            "football",
            bet_amount,
            0,
            football_value
        )
        
        await callback.message.answer(
            f"⚽ Выпало: {football_value}\n❌ Мимо ворот! Попробуйте еще раз\n"
            f"💎 Ваш баланс: {user.balance - bet_amount} звезд"
        )

async def play_bowling(callback: CallbackQuery, setting, bet_amount: int):
    message = await callback.message.answer_dice(emoji="🎳")
    bowling_value = message.dice.value
    
    # Получаем текущий баланс пользователя
    user = await db.get_user(callback.from_user.id)
    
    # Проверяем страйк (5-6 для победы)
    if bowling_value in WIN_VALUES["bowling"] and random.random() < setting.win_chance:
        win_amount = int(bet_amount * setting.win_multiplier)
        new_balance = await db.update_balance(
            callback.from_user.id, win_amount, "win", f"Выигрыш в bowling (выпало {bowling_value})"
        )
        await db.update_game_stat(
            callback.from_user.id, "bowling", bet_amount, win_amount
        )
        
        # Отправляем историю в чат
        await send_game_history(
            callback.from_user.id,
            callback.from_user.username,
            callback.from_user.first_name,
            "bowling",
            bet_amount,
            win_amount,
            bowling_value
        )
        
        await callback.message.answer(
            f"🎳 Выпало: {bowling_value}\n🎳 Страйк! Все кегли сбиты! Вы выиграли {win_amount} звезд!\n"
            f"💎 Ваш баланс: {new_balance} звезд"
        )
    else:
        await db.update_game_stat(callback.from_user.id, "bowling", bet_amount, 0)
        
        # Отправляем историю в чат
        await send_game_history(
            callback.from_user.id,
            callback.from_user.username,
            callback.from_user.first_name,
            "bowling",
            bet_amount,
            0,
            bowling_value
        )
        
        await callback.message.answer(
            f"🎳 Выпало: {bowling_value}\n💫 Не все кегли упали! Попробуйте еще раз\n"
            f"💎 Ваш баланс: {user.balance - bet_amount} звезд"
        )

async def play_slot(callback: CallbackQuery, setting, bet_amount: int):
    slot_message = await callback.message.answer_dice(emoji="🎰")
    await asyncio.sleep(4)
    
    slot_value = slot_message.dice.value
    
    # Получаем текущий баланс пользователя
    user = await db.get_user(callback.from_user.id)
    
    # Исправленная логика для рулетки - учитываем шанс выигрыша
    is_win = random.random() < setting.win_chance
    
    if is_win:
        if slot_value == 1:  # Джекпот
            win_amount = int(bet_amount * setting.win_multiplier * 5)
            win_type = "ДЖЕКПОТ"
        else:  # Обычный выигрыш
            win_amount = int(bet_amount * setting.win_multiplier)
            win_type = "Выигрыш"
        
        new_balance = await db.update_balance(
            callback.from_user.id, win_amount, "win", f"{win_type} в slot (выпало {slot_value})"
        )
        await db.update_game_stat(
            callback.from_user.id, "slot", bet_amount, win_amount
        )
        
        # Отправляем историю в чат
        await send_game_history(
            callback.from_user.id,
            callback.from_user.username,
            callback.from_user.first_name,
            "slot",
            bet_amount,
            win_amount,
            slot_value
        )
        
        await callback.message.answer(
            f"🎰 Выпало: {slot_value}\n🎉 {win_type}! Вы выиграли {win_amount} звезд! ✨\n"
            f"💎 Ваш баланс: {new_balance} звезд"
        )
    else:
        await db.update_game_stat(callback.from_user.id, "slot", bet_amount, 0)
        
        # Отправляем историю в чат
        await send_game_history(
            callback.from_user.id,
            callback.from_user.username,
            callback.from_user.first_name,
            "slot",
            bet_amount,
            0,
            slot_value
        )
        
        await callback.message.answer(
            f"🎰 Выпало: {slot_value}\n😢 К сожалению вы проиграли в этот раз, попробуйте еще, вдруг повезет\n"
            f"💎 Ваш баланс: {user.balance - bet_amount} звезд"
        )

@router.message(F.text == "🎰 Игры")
async def show_games(message: Message):
    await message.answer_photo(photo, caption="🎮 Выберите игру:", reply_markup=kb.games_menu())

@router.callback_query(F.data == 'back_to_games_list')
async def show_games2(callback:CallbackQuery, state:FSMContext):
    await state.clear()
    await callback.message.answer_photo(photo, caption="🎮 Выберите игру:", reply_markup=kb.games_menu())
    await callback.answer()

@router.callback_query(F.data.startswith("game_") or F.data == "back_to_games")
async def select_game(callback: CallbackQuery):
    game_type = callback.data.split("_")[1]
    user_id = callback.from_user.id
    
    # Получаем настройки игры
    setting = await db.get_game_setting(game_type)
    if not setting or not setting.is_active:
        await callback.answer("❌ Эта игра временно недоступна")
        return
    
    # Получаем пользователя
    user = await db.get_user(user_id)
    if not user:
        await callback.answer("❌ Пользователь не найден")
        return
    
    # Получаем текущую ставку пользователя
    user_bet = await db.get_user_bet(user_id, game_type)
    current_bet = user_bet.bet_amount if user_bet and user_bet.bet_amount > 0 else setting.cost
    
    # Формируем информационное сообщение
    game_info = f"""
{GAME_NAMES[game_type]}

💰 Ставка: {current_bet} звезд
🎯 Множитель: x{setting.win_multiplier}
🎲 Минимальная ставка: {setting.min_bet}
🎰 Максимальная ставка: {setting.max_bet}

📝 Условия победы:
{WIN_CONDITIONS[game_type]}

💎 Ваш баланс: {user.balance} звезд
"""

    if game_type == 'dice':
        await callback.message.answer_photo(photo, caption=game_info, reply_markup=kb.game_action_menu(game_type))
        await callback.answer()
    elif game_type == 'dart':
        await callback.message.answer_photo(photo, caption=game_info, reply_markup=kb.game_action_menu(game_type))
        await callback.answer()
    elif game_type == 'basketball':
        await callback.message.answer_photo(photo, caption=game_info, reply_markup=kb.game_action_menu(game_type))
        await callback.answer()
    elif game_type == 'football':
        await callback.message.answer_photo(photo, caption=game_info, reply_markup=kb.game_action_menu(game_type))
        await callback.answer()
    elif game_type == 'bowling':
        await callback.message.answer_photo(photo, caption=game_info, reply_markup=kb.game_action_menu(game_type))
        await callback.answer()
    elif game_type == 'slot':
        await callback.message.answer_photo(photo, caption=game_info, reply_markup=kb.game_action_menu(game_type))
        await callback.answer()

@router.callback_query(F.data.startswith("play_"))
async def play_game(callback: CallbackQuery):
    game_type = callback.data.split("_")[1]
    user_id = callback.from_user.id
    
    # Получаем настройки игры
    setting = await db.get_game_setting(game_type)
    if not setting or not setting.is_active:
        await callback.answer("❌ Эта игра временно недоступна")
        return
    
    # Получаем эффективную ставку (пользовательскую или стандартную)
    bet_amount = await db.get_effective_bet_amount(user_id, game_type)
    
    # Проверяем баланс
    user = await db.get_user(user_id)
    if not user or user.balance < bet_amount:
        await callback.answer("❌ Недостаточно звезд для игры")
        return
    
    # Списываем стоимость игры
    new_balance = await db.update_balance(
        user_id, -bet_amount, "bet", f"Ставка в игре {game_type}"
    )
    
    # Запускаем соответствующую игру
    if game_type == "dice":
        await play_dice(callback, setting, bet_amount)
    elif game_type == "dart":
        await play_dart(callback, setting, bet_amount)
    elif game_type == "basketball":
        await play_basketball(callback, setting, bet_amount)
    elif game_type == "football":
        await play_football(callback, setting, bet_amount)
    elif game_type == "bowling":
        await play_bowling(callback, setting, bet_amount)
    elif game_type == "slot":
        await play_slot(callback, setting, bet_amount)
    
    # Показываем кнопку "Назад к игре"
    await callback.message.answer(
        "🔄 Хотите сыграть еще раз?",
        reply_markup=kb.back_to_game_menu(game_type)
    )
    
    await callback.answer()

@router.callback_query(F.data.startswith("bet_"))
async def start_change_bet(callback: CallbackQuery, state: FSMContext):
    game_type = callback.data.split("_")[1]
    
    # Получаем настройки игры
    setting = await db.get_game_setting(game_type)
    if not setting:
        await callback.answer("❌ Настройки игры не найдены")
        return
    
    # Сохраняем тип игры в состоянии
    await state.update_data(game_type=game_type)
    await state.set_state(BetState.waiting_for_bet)
    
    await callback.message.answer(
        f"💰 Введите новую ставку для {GAME_NAMES[game_type]}\n\n"
        f"📊 Минимальная ставка: {setting.min_bet} звезд\n"
        f"📈 Максимальная ставка: {setting.max_bet} звезд\n\n"
        f"💎 Ваш текущий баланс: {(await db.get_user(callback.from_user.id)).balance} звезд\n\n"
        f"❌ Для отмены нажмите кнопку ниже",
        reply_markup=kb.cancel_keyboard()
    )
    await callback.answer()

@router.callback_query(StateFilter(BetState.waiting_for_bet), F.data == "cancel_keyboard")
async def cancel_bet_change(callback:CallbackQuery, state: FSMContext):
    data = await state.get_data()
    game_type = data.get('game_type', 'dice')
    await state.clear()
    await callback.answer()
    await callback.message.answer(
        "❌ Изменение ставки отменено",
        reply_markup=kb.back_to_game_menu(game_type)
    )

@router.message(StateFilter(BetState.waiting_for_bet))
async def process_bet_amount(message: Message, state: FSMContext):
    try:
        bet_amount = int(message.text)
        data = await state.get_data()
        game_type = data['game_type']
        
        # Устанавливаем пользовательскую ставку
        result = await db.set_user_bet(message.from_user.id, game_type, bet_amount)
        
        if result is True:
            await message.answer(
                f"✅ Ставка для {GAME_NAMES[game_type]} установлена: {bet_amount} звезд\n\n"
                f"Теперь при игре будет использоваться ваша персональная ставка",
                reply_markup=kb.back_to_game_menu(game_type)
            )
        elif result is False:
            setting = await db.get_game_setting(game_type)
            await message.answer(
                f"❌ Неверная ставка! Допустимый диапазон: {setting.min_bet}-{setting.max_bet} звезд\n\n"
                f"Попробуйте еще раз:",
                reply_markup=kb.cancel_keyboard()
            )
            return
        else:
            await message.answer(
                "❌ Ошибка при установке ставки",
                reply_markup=kb.back_to_game_menu(game_type)
            )
        
        await state.clear()
        
    except ValueError:
        await message.answer(
            "❌ Пожалуйста, введите число\n\n"
            "Пример: 10, 25, 50",
            reply_markup=kb.cancel_keyboard()
        )

@router.message(F.text == "📊 Статистика")
async def show_stats(message: Message):
    user = await db.get_user(message.from_user.id)
    if user:
        win_rate = (user.total_wins / user.total_bets * 100) if user.total_bets > 0 else 0
        stats_text = f"""
📊 Ваша статистика:
🎰 Всего игр: {user.total_bets}
🎯 Выигрышей: {user.total_wins}
📈 Win rate: {win_rate:.1f}%
💎 Баланс: {user.balance} звезд
"""
        await message.answer(stats_text)

@router.message(F.text == "ℹ️ Помощь")
async def show_help(message: Message):
    help_text = """
🎰 Правила:

💎 Звезды - это валюта для игры

🎮 Доступные игры:
  🎲 Кубик - выигрыш при 5 или 6
  🎯 Дартс - попадание в цель (5-6)
  🏀 Баскетбол - попадание в корзину (4-6)
  ⚽ Футбол - гол! (4-5)
  🎳 Боулинг - страйк! (5-6)
  🎰 Рулетка - игровой автомат

⚙️ Каждая игра имеет свою стоимость и шанс выигрыша.

🎰 Рулетка:
  🎯 Джекпот при значении 1 (5x множитель)
  🎯 Обычный выигрыш при других значениях

📋 По вопросам выводов писать 👉 @Helper_dice_man

🎯 Удачи в играх!
"""
    await message.answer(help_text)

@router.message(Command("history"))
async def show_recent_history(message: Message):
    """Показать последние игры (только для админов)"""
    if message.from_user.id not in ADMIN_IDS:  # Замените на ваш ID администратора
        await message.answer("❌ Доступ запрещен")
        return
    
    recent_games = await db.get_recent_games(10)
    
    if not recent_games:
        await message.answer("📊 История игр пуста")
        return
    
    history_text = "📊 <b>Последние 10 игр:</b>\n\n"
    
    for i, game in enumerate(recent_games, 1):
        game_emoji = GAME_EMOJIS.get(game['game_type'], "🎮")
        result_emoji = "🎉" if game['type'] == 'win' else "😢"
        
        history_text += f"{i}. {game_emoji} <b>{GAME_NAMES[game['game_type']]}</b>\n"
        history_text += f"   👤 {game['first_name']} (@{game['username'] or 'нет'})\n"
        history_text += f"   💰 Ставка: {abs(game['amount'])} звезд\n"
        history_text += f"   🎯 Результат: {result_emoji} {'ВЫИГРЫШ' if game['type'] == 'win' else 'ПРОИГРЫШ'}\n"
        
        if game['type'] == 'win':
            history_text += f"   🏆 Выигрыш: {game['amount']} звезд\n"
        
        history_text += f"   ⏰ {game['created_at'].strftime('%H:%M:%S')}\n"
        history_text += "   ─────────────────────\n"
    
    await message.answer(history_text, parse_mode="HTML")
