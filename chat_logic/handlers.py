import asyncio
import logging
from aiogram import F, Router, types
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.types import FSInputFile

import chat_logic.keyboards as kb
from database import db

router = Router()

@router.message(Command('help'))
async def help(message: types.Message):
    if message.chat.type not in ["group", "supergroup"]:
        return
    
    photo = FSInputFile('photos/SuperDice.png')
    text = '''🎉 Добро пожаловать в бот SuperDice

⭐ Как начать играть:

1. Введите одну из доступных команд.
2. Игрок, которому вы предложили игру, принимает её, нажав кнопку.
3. Бот поочередно отправляет выбранный эмодзи.
4. Кто набрал больше очков, тот и побеждает.

‼️ Для ставки пополните баланс в боте.

📋 Доступные команды для этого чата 👇

/dice @username ставка
/darts @username ставка
/basket @username ставка
/football @username ставка
/bowling @username ставка
/roulette @username ставка
'''

    await message.answer_photo(photo, caption=text)

@router.message(Command('dice'))
async def play_dice(message: types.Message):
    if message.chat.type not in ["group", "supergroup"]:
        return
    
    creator = f'@{message.from_user.username}'
    invited = message.text.split()[1]
    price = int(message.text.split()[2])

    creator_info = await db.get_user_by_username(creator.split('@')[1])
    invited_info = await db.get_user_by_username(invited.split('@')[1])

    if creator_info.user_id == invited_info.user_id:
        await message.answer('❌ Вы не можете создать игру с самим собой')
        return

    if creator_info and invited_info:
        if creator_info.balance >= price and invited_info.balance >= price:
            game_id = await db.create_game_chat('dice', creator_info.user_id, invited_info.user_id, price)
            await db.add_stars_to_user_by_userid(creator_info.user_id, int(f'-{price}'))

            await message.answer(f'''👥 ИГРА СОЗДАНА

👤 Игроки:
{creator}   {invited}

🏦 Ставка:
{price}
''', reply_markup=await kb.start_game(invited_info.user_id, game_id))

        else:
            await message.answer('❌ Недостаточный баланс для создания игры. \n\nПополнить баланс можно тут 👇 \n@adsdasadsadsasddsaasdads_bot')
    else:
        await message.answer('❌ Один из участников на авторизован. \n\nЗапустите бота 👇 \n@adsdasadsadsasddsaasdads_bot')

@router.callback_query(F.data.startswith('game_'))
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

    if type == 'start':

        if callback.from_user.id != invited_id:
            await callback.answer('❌ Эта кнопка не для вас')
            return
        
        await db.add_stars_to_user_by_userid(invited_id, int(f'-{game_info.price}'))

        await callback.answer()
        await callback.message.edit_text(f'✅ Игра началась \n\nПервым ходит создатель: @{creator_info.username}')

        message = await callback.message.answer_dice(emoji="🎲")
        dice_value_first = message.dice.value

        await asyncio.sleep(1)

        message = await callback.message.answer_dice(emoji="🎲")
        dice_value_first += message.dice.value

        await asyncio.sleep(5)
        await callback.message.answer(f'Сумма очков @{creator_info.username}: {dice_value_first}')

        message = await callback.message.answer_dice(emoji="🎲")
        dice_value_second = message.dice.value

        await asyncio.sleep(1)

        message = await callback.message.answer_dice(emoji="🎲")
        dice_value_second += message.dice.value

        await asyncio.sleep(5)
        await callback.message.answer(f'Сумма очков @{invited_info.username}: {dice_value_second}')

        if dice_value_first == dice_value_second:
            await callback.message.answer('😌 Сегодня без победителя. Средства возвращены.')
            await db.add_stars_to_user_by_userid(creator_info.user_id, game_info.price)
            await db.add_stars_to_user_by_userid(invited_id, game_info.price)

        if dice_value_first > dice_value_second:
            await callback.message.answer(f'✅ Победитель: @{creator_info.username}. Выигрыш начислен. Сыграем ещё?')
            await db.add_stars_to_user_by_userid(creator_info.user_id, game_info.price*2)

        if dice_value_first < dice_value_second:
            await callback.message.answer(f'✅ Победитель: @{invited_info.username}. Выигрыш начислен. Сыграем ещё?')
            await db.add_stars_to_user_by_userid(invited_id, game_info.price*2)


        try:
            await db.update_chat_game_status(game_id, 'completed')
        except ValueError as e:
            logging.error(f'❌ Ошибка обновления статуса: {e}')

    if type == 'rejected':

        if callback.from_user.id != invited_id and callback.from_user.id != int(creator_info.user_id):
            await callback.answer('❌ Эта кнопка не для вас')
            return

        await callback.message.edit_text('❌ Игра отклонена. Звезды возвращены на баланс создателя.')

        await db.add_stars_to_user_by_userid(creator_info.user_id, game_info.price)

        try:
            await db.update_chat_game_status(game_id, 'rejected')
        except ValueError as e:
            logging.error(f'❌ Ошибка обновления статуса: {e}')
        