import asyncio
import logging
from aiogram import F, Router, types
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.types import FSInputFile
from config import HISTORY_CHAT_ID, bot
from datetime import datetime

import chat_logic.keyboards as kb
from database import db

router = Router()

GAME_NAMES = {
    'dice': 'Кубик',
    'darts': 'Дартс',
    'basket': 'Баскетбол',
    'football': 'Футбол',
    'bowling': 'Боулинг',
    'roulette': 'Рулетка'

}

GAME_EMOJIS = {
    "dice": "🎲",
    "darts": "🎯",
    "basket": "🏀",
    "football": "⚽",
    "bowling": "🎳",
    "roulette": "🎰"
}

async def send_game_history(username_creator: str, first_name_creator: str, username_invited: str, first_name_invited: str, winner: str, game_type: str, bet_amount: int):
    try:
        if HISTORY_CHAT_ID:
            history_message = f"""
{GAME_EMOJIS[game_type]} <b>ИГРА В ЧАТЕ ЗАВЕРШЕНА</b> {GAME_EMOJIS[game_type]}

👤 <b>Игрок1:</b> {first_name_creator} (@{username_creator if username_creator else 'нет username'})
👤 <b>Игрок2:</b> {first_name_invited} (@{username_invited if username_invited else 'нет username'})
🎮 <b>Игра:</b> {GAME_EMOJIS[game_type]} {GAME_NAMES[game_type]}
💰 <b>Ставка:</b> {bet_amount} звезд

🎯 <b>Результат:</b> {winner}
⏰ <b>Время:</b> {datetime.now().strftime('%H:%M:%S')}
"""
            
            await bot.send_message(
                chat_id=HISTORY_CHAT_ID,
                text=history_message,
                parse_mode="HTML"
            )
    except Exception as e:
        print(f"Ошибка при отправке истории в чат: {e}")

@router.message(Command('help'))
async def help(message: types.Message):
    user = await db.get_user(message.from_user.id)

    if user.banned:
        await message.answer('❌ Доступ запрещен, вы забанены в данном боте')
        return

    if message.chat.type not in ["group", "supergroup"]:
        return
    
    photo = FSInputFile('photos/SuperDice.png')
    text = '''🎉 Добро пожаловать в бот SuperDice

⭐ Как начать играть:

1. Введите одну из доступных команд.
2. Игрок, которому вы предложили игру, принимает её, нажав кнопку.
3. Бот поочередно отправляет выбранный эмодзи.
4. Кто набрал больше очков, тот и побеждает.

‼️ Для ставки пополните баланс в <a href='https://t.me/adsdasadsadsasddsaasdads_bot?start=deposit'>боте</a>.

📋 Доступные команды для этого чата 👇

/dice @username ставка
/darts @username ставка
/basket @username ставка
/football @username ставка
/bowling @username ставка
/roulette @username ставка
'''

    await message.answer_photo(photo, caption=text, parse_mode='HTML')

@router.message(Command('dice'))
async def play_dice(message: types.Message):
    if message.chat.type not in ["group", "supergroup"]:
        return
    
    game = message.text[1:].split()[0]
    creator = f'@{message.from_user.username}'
    invited = message.text.split()[1]
    price = int(message.text.split()[2])

    creator_info = await db.get_user_by_username(creator.split('@')[1])
    invited_info = await db.get_user_by_username(invited.split('@')[1])

    if creator_info.banned or invited_info.banned:
        await message.answer('❌ Доступ запрещен, один из участников забанен в боте')
        return

    if creator_info.user_id == invited_info.user_id:
        await message.answer('❌ Вы не можете создать игру с самим собой')
        return

    if creator_info and invited_info:
        if creator_info.balance >= price and invited_info.balance >= price:
            game_id = await db.create_game_chat(game, creator_info.user_id, invited_info.user_id, price)
            await db.add_stars_to_user_by_userid(creator_info.user_id, int(f'-{price}'), 'bet', 'Заморозка на время игры')

            await message.answer(f'''👥 ИГРА {GAME_NAMES[game]} СОЗДАНА

👤 Игроки:
{creator}   {invited}

🏦 Ставка:
{price}

‼️ Время на подтверждение - 5 минут
''', reply_markup=await kb.start_game(invited_info.user_id, game_id))

        else:
            await message.answer('❌ Недостаточный баланс для создания игры. \n\nПополнить баланс можно тут 👇 \n<a href="https://t.me/adsdasadsadsasddsaasdads_bot?start=deposit">Наш бот</a>')
    else:
        await message.answer('❌ Один из участников на авторизован. \n\nЗапустите бота 👇 \n<a href="https://t.me/adsdasadsadsasddsaasdads_bot?start=start">Наш бот</a>')

@router.message(Command('darts'))
async def play_dice(message: types.Message):
    if message.chat.type not in ["group", "supergroup"]:
        return
    
    game = message.text[1:].split()[0]
    creator = f'@{message.from_user.username}'
    invited = message.text.split()[1]
    price = int(message.text.split()[2])

    creator_info = await db.get_user_by_username(creator.split('@')[1])
    invited_info = await db.get_user_by_username(invited.split('@')[1])

    if creator_info.banned or invited_info.banned:
        await message.answer('❌ Доступ запрещен, один из участников забанен в боте')
        return

    if creator_info.user_id == invited_info.user_id:
        await message.answer('❌ Вы не можете создать игру с самим собой')
        return

    if creator_info and invited_info:
        if creator_info.balance >= price and invited_info.balance >= price:
            game_id = await db.create_game_chat(game, creator_info.user_id, invited_info.user_id, price)
            await db.add_stars_to_user_by_userid(creator_info.user_id, int(f'-{price}'), 'bet', 'Заморозка на время игры')

            await message.answer(f'''👥 ИГРА {GAME_NAMES[game]} СОЗДАНА

👤 Игроки:
{creator}   {invited}

🏦 Ставка:
{price}

‼️ Время на подтверждение - 5 минут
''', reply_markup=await kb.start_game(invited_info.user_id, game_id))

        else:
            await message.answer('❌ Недостаточный баланс для создания игры. \n\nПополнить баланс можно тут 👇 \n<a href="https://t.me/adsdasadsadsasddsaasdads_bot?start=deposit">Наш бот</a>')
    else:
        await message.answer('❌ Один из участников на авторизован. \n\nЗапустите бота 👇 \n<a href="https://t.me/adsdasadsadsasddsaasdads_bot?start=start">Наш бот</a>')

@router.message(Command('basket'))
async def play_dice(message: types.Message):
    if message.chat.type not in ["group", "supergroup"]:
        return
    
    game = message.text[1:].split()[0]
    creator = f'@{message.from_user.username}'
    invited = message.text.split()[1]
    price = int(message.text.split()[2])

    creator_info = await db.get_user_by_username(creator.split('@')[1])
    invited_info = await db.get_user_by_username(invited.split('@')[1])

    if creator_info.banned or invited_info.banned:
        await message.answer('❌ Доступ запрещен, один из участников забанен в боте')
        return

    if creator_info.user_id == invited_info.user_id:
        await message.answer('❌ Вы не можете создать игру с самим собой')
        return

    if creator_info and invited_info:
        if creator_info.balance >= price and invited_info.balance >= price:
            game_id = await db.create_game_chat(game, creator_info.user_id, invited_info.user_id, price)
            await db.add_stars_to_user_by_userid(creator_info.user_id, int(f'-{price}'), 'bet', 'Заморозка на время игры')

            await message.answer(f'''👥 ИГРА {GAME_NAMES[game]} СОЗДАНА

👤 Игроки:
{creator}   {invited}

🏦 Ставка:
{price}

‼️ Время на подтверждение - 5 минут
''', reply_markup=await kb.start_game(invited_info.user_id, game_id))

        else:
            await message.answer('❌ Недостаточный баланс для создания игры. \n\nПополнить баланс можно тут 👇 \n<a href="https://t.me/adsdasadsadsasddsaasdads_bot?start=deposit">Наш бот</a>')
    else:
        await message.answer('❌ Один из участников на авторизован. \n\nЗапустите бота 👇 \n<a href="https://t.me/adsdasadsadsasddsaasdads_bot?start=start">Наш бот</a>')

@router.message(Command('football'))
async def play_dice(message: types.Message):
    if message.chat.type not in ["group", "supergroup"]:
        return
    
    game = message.text[1:].split()[0]
    creator = f'@{message.from_user.username}'
    invited = message.text.split()[1]
    price = int(message.text.split()[2])

    creator_info = await db.get_user_by_username(creator.split('@')[1])
    invited_info = await db.get_user_by_username(invited.split('@')[1])

    if creator_info.banned or invited_info.banned:
        await message.answer('❌ Доступ запрещен, один из участников забанен в боте')
        return

    if creator_info.user_id == invited_info.user_id:
        await message.answer('❌ Вы не можете создать игру с самим собой')
        return

    if creator_info and invited_info:
        if creator_info.balance >= price and invited_info.balance >= price:
            game_id = await db.create_game_chat(game, creator_info.user_id, invited_info.user_id, price)
            await db.add_stars_to_user_by_userid(creator_info.user_id, int(f'-{price}'), 'bet', 'Заморозка на время игры')

            await message.answer(f'''👥 ИГРА {GAME_NAMES[game]} СОЗДАНА

👤 Игроки:
{creator}   {invited}

🏦 Ставка:
{price}

‼️ Время на подтверждение - 5 минут
''', reply_markup=await kb.start_game(invited_info.user_id, game_id))

        else:
            await message.answer('❌ Недостаточный баланс для создания игры. \n\nПополнить баланс можно тут 👇 \n<a href="https://t.me/adsdasadsadsasddsaasdads_bot?start=deposit">Наш бот</a>')
    else:
        await message.answer('❌ Один из участников на авторизован. \n\nЗапустите бота 👇 \n<a href="https://t.me/adsdasadsadsasddsaasdads_bot?start=start">Наш бот</a>')


@router.message(Command('bowling'))
async def play_dice(message: types.Message):
    if message.chat.type not in ["group", "supergroup"]:
        return
    
    game = message.text[1:].split()[0]
    creator = f'@{message.from_user.username}'
    invited = message.text.split()[1]
    price = int(message.text.split()[2])

    creator_info = await db.get_user_by_username(creator.split('@')[1])
    invited_info = await db.get_user_by_username(invited.split('@')[1])

    if creator_info.banned or invited_info.banned:
        await message.answer('❌ Доступ запрещен, один из участников забанен в боте')
        return

    if creator_info.user_id == invited_info.user_id:
        await message.answer('❌ Вы не можете создать игру с самим собой')
        return

    if creator_info and invited_info:
        if creator_info.balance >= price and invited_info.balance >= price:
            game_id = await db.create_game_chat(game, creator_info.user_id, invited_info.user_id, price)
            await db.add_stars_to_user_by_userid(creator_info.user_id, int(f'-{price}'), 'bet', 'Заморозка на время игры')

            await message.answer(f'''👥 ИГРА {GAME_NAMES[game]} СОЗДАНА

👤 Игроки:
{creator}   {invited}

🏦 Ставка:
{price}

‼️ Время на подтверждение - 5 минут
''', reply_markup=await kb.start_game(invited_info.user_id, game_id))

        else:
            await message.answer('❌ Недостаточный баланс для создания игры. \n\nПополнить баланс можно тут 👇 \n<a href="https://t.me/adsdasadsadsasddsaasdads_bot?start=deposit">Наш бот</a>')
    else:
        await message.answer('❌ Один из участников на авторизован. \n\nЗапустите бота 👇 \n<a href="https://t.me/adsdasadsadsasddsaasdads_bot?start=start">Наш бот</a>')

@router.message(Command('roulette'))
async def play_dice(message: types.Message):
    if message.chat.type not in ["group", "supergroup"]:
        return
    
    game = message.text[1:].split()[0]
    creator = f'@{message.from_user.username}'
    invited = message.text.split()[1]
    price = int(message.text.split()[2])

    creator_info = await db.get_user_by_username(creator.split('@')[1])
    invited_info = await db.get_user_by_username(invited.split('@')[1])

    if creator_info.banned or invited_info.banned:
        await message.answer('❌ Доступ запрещен, один из участников забанен в боте')
        return

    if creator_info.user_id == invited_info.user_id:
        await message.answer('❌ Вы не можете создать игру с самим собой')
        return

    if creator_info and invited_info:
        if creator_info.balance >= price and invited_info.balance >= price:
            game_id = await db.create_game_chat(game, creator_info.user_id, invited_info.user_id, price)
            await db.add_stars_to_user_by_userid(creator_info.user_id, int(f'-{price}'), 'bet', 'Заморозка на время игры')

            await message.answer(f'''👥 ИГРА {GAME_NAMES[game]} СОЗДАНА

👤 Игроки:
{creator}   {invited}

🏦 Ставка:
{price}

‼️ Время на подтверждение - 5 минут
''', reply_markup=await kb.start_game(invited_info.user_id, game_id))

        else:
            await message.answer('❌ Недостаточный баланс для создания игры. \n\nПополнить баланс можно тут 👇 \n<a href="https://t.me/adsdasadsadsasddsaasdads_bot?start=deposit">Наш бот</a>')
    else:
        await message.answer('❌ Один из участников на авторизован. \n\nЗапустите бота 👇 \n<a href="https://t.me/adsdasadsadsasddsaasdads_bot?start=start">Наш бот</a>')

@router.callback_query(F.data.startswith('gamechat_'))
async def start_game_chat(callback: types.CallbackQuery):
    type = callback.data.split('_')[1]
    invited_id = int(callback.data.split('_')[2])
    game_id = callback.data.split('_')[3]

    game_info = await db.get_chat_game_by_id(game_id)

    if not game_info:
        await callback.answer("❌ Игра не найдена", show_alert=True)
        return

    creator_info = await db.get_user(game_info.creator)
    invited_info = await db.get_user(game_info.invited)

    if creator_info.banned or invited_info.banned:
        await message.answer('❌ Доступ запрещен, один из участников забанен в боте')
        return

    if type == 'start':

        if game_info.status == 'rejected':
            await callback.answer('❌ Истек срок принятия игры. Звезды возвращены на баланс создателя')
            return

        if callback.from_user.id != invited_id:
            await callback.answer('❌ Эта кнопка не для вас')
            return
        
        await db.add_stars_to_user_by_userid(invited_info.user_id, int(f'-{game_info.price}'), 'bet', 'Заморозка на время игры')

        await callback.answer()
        await callback.message.edit_text(f'✅ Игра началась \n\nПервым ходит создатель: @{creator_info.username}')

        if game_info.game == 'dice':

            message = await callback.message.answer_dice(emoji="🎲")
            value_first = message.dice.value

            await asyncio.sleep(1)

            message = await callback.message.answer_dice(emoji="🎲")
            value_first += message.dice.value

            await asyncio.sleep(5)
            await callback.message.answer(f'Сумма очков @{creator_info.username}: {value_first}')

            message = await callback.message.answer_dice(emoji="🎲")
            value_second = message.dice.value

            await asyncio.sleep(1)

            message = await callback.message.answer_dice(emoji="🎲")
            value_second += message.dice.value

            await asyncio.sleep(5)
            await callback.message.answer(f'Сумма очков @{invited_info.username}: {value_second}')

        if game_info.game == 'darts':

            message = await callback.message.answer_dice(emoji="🎯")
            value_first = message.dice.value

            await asyncio.sleep(1)

            message = await callback.message.answer_dice(emoji="🎯")
            value_first += message.dice.value

            await asyncio.sleep(5)
            await callback.message.answer(f'Сумма очков @{creator_info.username}: {value_first}')

            message = await callback.message.answer_dice(emoji="🎯")
            value_second = message.dice.value

            await asyncio.sleep(1)

            message = await callback.message.answer_dice(emoji="🎯")
            value_second += message.dice.value

            await asyncio.sleep(5)
            await callback.message.answer(f'Сумма очков @{invited_info.username}: {value_second}')

        if game_info.game == 'basket':
            
            message = await callback.message.answer_dice(emoji="🏀")
            value_first = message.dice.value

            await asyncio.sleep(1)

            message = await callback.message.answer_dice(emoji="🏀")
            value_first += message.dice.value

            await asyncio.sleep(5)
            await callback.message.answer(f'Сумма очков @{creator_info.username}: {value_first}')

            message = await callback.message.answer_dice(emoji="🏀")
            value_second = message.dice.value

            await asyncio.sleep(1)

            message = await callback.message.answer_dice(emoji="🏀")
            value_second += message.dice.value

            await asyncio.sleep(5)
            await callback.message.answer(f'Сумма очков @{invited_info.username}: {value_second}')

        if game_info.game == 'football':
            
            message = await callback.message.answer_dice(emoji="⚽")
            value_first = message.dice.value

            await asyncio.sleep(1)

            message = await callback.message.answer_dice(emoji="⚽")
            value_first += message.dice.value

            await asyncio.sleep(5)
            await callback.message.answer(f'Сумма очков @{creator_info.username}: {value_first}')

            message = await callback.message.answer_dice(emoji="⚽")
            value_second = message.dice.value

            await asyncio.sleep(1)

            message = await callback.message.answer_dice(emoji="⚽")
            value_second += message.dice.value

            await asyncio.sleep(5)
            await callback.message.answer(f'Сумма очков @{invited_info.username}: {value_second}')

        if game_info.game == 'bowling':
            
            message = await callback.message.answer_dice(emoji="🎳")
            value_first = message.dice.value

            await asyncio.sleep(1)

            message = await callback.message.answer_dice(emoji="🎳")
            value_first += message.dice.value

            await asyncio.sleep(5)
            await callback.message.answer(f'Сумма очков @{creator_info.username}: {value_first}')

            message = await callback.message.answer_dice(emoji="🎳")
            value_second = message.dice.value

            await asyncio.sleep(1)

            message = await callback.message.answer_dice(emoji="🎳")
            value_second += message.dice.value

            await asyncio.sleep(5)
            await callback.message.answer(f'Сумма очков @{invited_info.username}: {value_second}')

        if game_info.game == 'roulette':
            
            message = await callback.message.answer_dice(emoji="🎰")
            value_first = message.dice.value

            await asyncio.sleep(1)

            message = await callback.message.answer_dice(emoji="🎰")
            value_first += message.dice.value

            await asyncio.sleep(5)
            await callback.message.answer(f'Сумма очков @{creator_info.username}: {value_first}')

            message = await callback.message.answer_dice(emoji="🎰")
            value_second = message.dice.value

            await asyncio.sleep(1)

            message = await callback.message.answer_dice(emoji="🎰")
            value_second += message.dice.value

            await asyncio.sleep(5)
            await callback.message.answer(f'Сумма очков @{invited_info.username}: {value_second}')

        winner = ''

        setting = await db.get_chat_game_setting(game_info.game)

        if value_first == value_second:
            winner = 'Ничья'
            await callback.message.answer('😌 Сегодня без победителя. Средства возвращены.')
            await db.add_stars_to_user_by_userid(creator_info.user_id, game_info.price, 'return', 'Ничья в чате')
            await db.add_stars_to_user_by_userid(invited_info.user_id, game_info.price, 'return', 'Ничья в чате')

        if value_first > value_second:
            winner = creator_info.username
            await callback.message.answer(f'✅ Победитель: @{creator_info.username}. Выигрыш начислен. Сыграем ещё?')
            await db.add_stars_to_user_by_userid(creator_info.user_id, (game_info.price*2)* (1 - setting.commission / 100), 'win', 'Победа в чате')

        if value_first < value_second:
            winner = invited_info.username
            await callback.message.answer(f'✅ Победитель: @{invited_info.username}. Выигрыш начислен. Сыграем ещё?')
            await db.add_stars_to_user_by_userid(invited_info.user_id, (game_info.price*2)* (1 - setting.commission / 100), 'win', 'Победа в чате')


        try:
            await db.update_chat_game_status(game_id, 'completed')
            await send_game_history(
                creator_info.username, 
                creator_info.first_name, 
                invited_info.username, 
                invited_info.first_name, 
                winner, 
                game_info.game, 
                game_info.price
            )
            
        except ValueError as e:
            logging.error(f'❌ Ошибка обновления статуса: {e}')

    if type == 'rejected':

        if callback.from_user.id != invited_id and callback.from_user.id != int(creator_info.user_id):
            await callback.answer('❌ Эта кнопка не для вас')
            return

        await callback.message.edit_text('❌ Игра отклонена. Звезды возвращены на баланс создателя.')

        await db.add_stars_to_user_by_userid(creator_info.user_id, game_info.price, 'return', 'Отмена игры')

        try:
            await db.update_chat_game_status(game_id, 'rejected')
        except ValueError as e:
            logging.error(f'❌ Ошибка обновления статуса: {e}')
        