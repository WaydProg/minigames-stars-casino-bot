import asyncio
from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from config import ADMIN_IDS
from database import db
from sqlalchemy import select
from aiogram.fsm.context import FSMContext
from config import bot
from aiogram.methods import GetAvailableGifts, SendGift

import states as states
import keyboards as kb

router = Router()

@router.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Доступ запрещен")
        return
    
    await message.answer("👨‍💻 Панель администратора:", reply_markup=kb.admin_menu())

@router.message(Command("settings"))
async def show_current_settings(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    settings = await db.get_all_settings()
    settings_text = "⚙️ Текущие настройки игр:\n\n"
    
    for setting in settings:
        status = "✅ Активна" if setting.is_active else "❌ Неактивна"
        settings_text += f"""
🎮 {setting.game_type.upper()}:
   🎲 Шанс выигрыша: {setting.win_chance * 100}%
   💰 Стоимость: {setting.cost} звезд
   🎯 Множитель: x{setting.win_multiplier}
   📊 Мин. ставка: {setting.min_bet}
   📈 Макс. ставка: {setting.max_bet}
   🔒 Статус: {status}
------------------------
"""
    
    await message.answer(settings_text)

@router.callback_query(F.data == "admin_settings")
async def game_settings(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    
    await callback.message.edit_text(
        "⚙️ Настройки игр:", 
        reply_markup=kb.game_settings_menu()
    )

@router.callback_query(F.data.startswith("setting_"))
async def edit_game_setting(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    
    game_type = callback.data.split("_")[1]
    setting = await db.get_game_setting(game_type)
    
    if not setting:
        await callback.answer("❌ Настройки для этой игры не найдены")
        return
    
    text = f"""
⚙️ Настройки {game_type.upper()}:

🎲 Шанс выигрыша: {setting.win_chance * 100}%
💰 Стоимость: {setting.cost} звезд
🎯 Множитель: x{setting.win_multiplier}
📊 Минимальная ставка: {setting.min_bet}
📈 Максимальная ставка: {setting.max_bet}
🔒 Статус: {'✅ Активна' if setting.is_active else '❌ Неактивна'}

📝 Команды для изменения:

/chance_{game_type} [0.1-1.0] - изменить шанс выигрыша
/cost_{game_type} [число] - изменить стоимость
/multiplier_{game_type} [число] - изменить множитель
/minbet_{game_type} [число] - изменить мин. ставку
/maxbet_{game_type} [число] - изменить макс. ставку
/toggle_{game_type} - включить/выключить игру

Пример: /chance_dice 0.5
"""
    await callback.message.edit_text(text, reply_markup=kb.back_to_admin())

@router.message(F.text.startswith("/chance_"))
async def change_chance(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    try:
        parts = message.text.split()
        game_type = parts[0].split("_")[1]
        chance = float(parts[1])
        
        if 0 <= chance <= 1:
            await db.update_game_setting(game_type, win_chance=chance)
            await message.answer(f"✅ Шанс выигрыша для {game_type} изменен на {chance * 100}%")
        else:
            await message.answer("❌ Шанс должен быть от 0 до 1")
    except (IndexError, ValueError):
        await message.answer("❌ Неверный формат команды. Используйте: /chance_[игра] [0.1-1.0]")

@router.message(F.text.startswith("/cost_"))
async def change_cost(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    try:
        parts = message.text.split()
        game_type = parts[0].split("_")[1]
        cost = int(parts[1])
        
        if cost > 0:
            await db.update_game_setting(game_type, cost=cost)
            await message.answer(f"✅ Стоимость {game_type} изменена на {cost} звезд")
        else:
            await message.answer("❌ Стоимость должна быть положительной")
    except (IndexError, ValueError):
        await message.answer("❌ Неверный формат команды. Используйте: /cost_[игра] [число]")

@router.message(F.text.startswith("/multiplier_"))
async def change_multiplier(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    try:
        parts = message.text.split()
        game_type = parts[0].split("_")[1]
        multiplier = float(parts[1])
        
        if multiplier > 0:
            await db.update_game_setting(game_type, win_multiplier=multiplier)
            await message.answer(f"✅ Множитель для {game_type} изменен на {multiplier}")
        else:
            await message.answer("❌ Множитель должен быть положительным")
    except (IndexError, ValueError):
        await message.answer("❌ Неверный формат команды. Используйте: /multiplier_[игра] [число]")

@router.message(F.text.startswith("/minbet_"))
async def change_min_bet(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    try:
        parts = message.text.split()
        game_type = parts[0].split("_")[1]
        min_bet = int(parts[1])
        
        if min_bet > 0:
            await db.update_game_setting(game_type, min_bet=min_bet)
            await message.answer(f"✅ Минимальная ставка для {game_type} изменена на {min_bet}")
        else:
            await message.answer("❌ Минимальная ставка должна быть положительной")
    except (IndexError, ValueError):
        await message.answer("❌ Неверный формат команды. Используйте: /minbet_[игра] [число]")

@router.message(F.text.startswith("/maxbet_"))
async def change_max_bet(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    try:
        parts = message.text.split()
        game_type = parts[0].split("_")[1]
        max_bet = int(parts[1])
        
        if max_bet > 0:
            await db.update_game_setting(game_type, max_bet=max_bet)
            await message.answer(f"✅ Максимальная ставка для {game_type} изменена на {max_bet}")
        else:
            await message.answer("❌ Максимальная ставка должна быть положительной")
    except (IndexError, ValueError):
        await message.answer("❌ Неверный формат команды. Используйте: /maxbet_[игра] [число]")

@router.message(F.text.startswith("/toggle_"))
async def toggle_game(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    try:
        game_type = message.text.split("_")[1]
        setting = await db.get_game_setting(game_type)
        if setting:
            new_status = not setting.is_active
            await db.update_game_setting(game_type, is_active=new_status)
            status = "активна" if new_status else "неактивна"
            await message.answer(f"✅ Игра {game_type} теперь {status}")
        else:
            await message.answer("❌ Игра не найдена")
    except IndexError:
        await message.answer("❌ Неверный формат команды. Используйте: /toggle_[игра]")

@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    
    users = await db.get_all_users()
    total_users = len(users)
    total_balance = sum(user.balance for user in users)
    total_bets = sum(user.total_bets for user in users)
    total_wins = sum(user.total_wins for user in users)
    
    # Статистика по доходам
    total_income = total_bets - total_wins if total_bets > total_wins else 0
    
    text = f"""
📊 Статистика:

👥 Всего пользователей: {total_users}
💎 Общий баланс звезд: {total_balance}
🎰 Всего ставок: {total_bets}
🎯 Всего выигрышей: {total_wins}
💰 Доход: {total_income} звезд
📈 Win rate: {total_wins/total_bets*100 if total_bets > 0 else 0:.1f}%

📊 Активные пользователи: {sum(1 for user in users if user.total_bets > 0)}
"""
    await callback.message.edit_text(text, reply_markup=kb.back_to_admin())

@router.callback_query(F.data == "admin_users")
async def admin_users(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    
    users = await db.get_all_users()
    users_text = "👥 Список пользователей (первые 10):\n\n"
    
    # Сортируем пользователей по балансу (по убыванию)
    sorted_users = sorted(users, key=lambda x: x.balance, reverse=True)
    
    for i, user in enumerate(sorted_users[:10], 1):
        win_rate = (user.total_wins / user.total_bets * 100) if user.total_bets > 0 else 0
        users_text += f"{i}. 👤 {user.first_name}"
        if user.username:
            users_text += f" (@{user.username})"
        users_text += f"\n   ID: {user.user_id}\n"
        users_text += f"   💎 Баланс: {user.balance} звезд\n"
        users_text += f"   🎰 Игр: {user.total_bets} | 🎯 Побед: {user.total_wins}\n"
        users_text += f"   📈 Win rate: {win_rate:.1f}%\n"
        users_text += "   ─────────────────────\n"
    
    if len(users) > 10:
        users_text += f"\n... и еще {len(users) - 10} пользователей"
    
    await callback.message.edit_text(users_text, reply_markup=kb.back_to_admin())

@router.callback_query(F.data == "admin_add_stars")
async def admin_add_stars(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    
    await callback.message.edit_text(
        "💎 Управление звездами пользователей:\n\n"
        "Добавить звезды:\n"
        "/addstars [username] [amount]\n\n"
        "Убрать звезды:\n"
        "/removestars [username] [amount]\n\n"
        "Установить баланс:\n"
        "/setbalance [username] [amount]\n\n"
        "Примеры:\n"
        "/addstars @username 100\n"
        "/removestars @username 50\n"
        "/setbalance @username 200",
        reply_markup=kb.back_to_admin()
    )

@router.message(F.text.startswith("/addstars"))
async def add_stars_to_user(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    try:
        parts = message.text.split()
        username = parts[1]
        amount = int(parts[2])
        
        if amount <= 0:
            await message.answer("❌ Количество звезд должно быть положительным")
            return
        
        new_balance = await db.add_stars_to_user(username.split('@')[1], amount)
        if new_balance is not None:
            await message.answer(f"✅ Добавлено {amount} звезд пользователю {username}\nНовый баланс: {new_balance} звезд")
        else:
            await message.answer("❌ Пользователь не найден")
    except (IndexError, ValueError):
        await message.answer("❌ Неверный формат команды. Используйте: /addstars [username] [amount]")

@router.message(F.text.startswith("/removestars"))
async def remove_stars_from_user(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    try:
        parts = message.text.split()
        username = parts[1]
        amount = int(parts[2])
        
        if amount <= 0:
            await message.answer("❌ Количество звезд должно быть положительным")
            return
        
        # Добавляем отрицательное количество звезд
        new_balance = await db.add_stars_to_user(username.split('@')[1], -amount)
        if new_balance is not None:
            await message.answer(f"✅ Убрано {amount} звезд у пользователя {username}\nНовый баланс: {new_balance} звезд")
        else:
            await message.answer("❌ Пользователь не найден")
    except (IndexError, ValueError):
        await message.answer("❌ Неверный формат команды. Используйте: /removestars [username] [amount]")

@router.message(F.text.startswith("/setbalance"))
async def set_user_balance(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    try:
        parts = message.text.split()
        username = parts[1]
        amount = int(parts[2])
        
        if amount < 0:
            await message.answer("❌ Баланс не может быть отрицательным")
            return
        
        user = await db.get_user_by_username(username.split('@')[1])
        if user:
            # Вычисляем разницу для установки точного баланса
            difference = amount - user.balance
            new_balance = await db.add_stars_to_user(username.split('@')[1], difference)
            await message.answer(f"✅ Баланс пользователя {username} установлен на {new_balance} звезд")
        else:
            await message.answer("❌ Пользователь не найден")
    except (IndexError, ValueError):
        await message.answer("❌ Неверный формат команды. Используйте: /setbalance [user_id] [amount]")

@router.message(Command("games_history"))
async def show_games_history(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    recent_games = await db.get_recent_games(20)
    
    if not recent_games:
        await message.answer("📊 История игр пуста")
        return
    
    history_text = "📊 <b>Последние 20 игр:</b>\n\n"
    
    for i, game in enumerate(recent_games, 1):
        game_emoji = "🎲" if game['game_type'] == 'dice' else \
                    "🎯" if game['game_type'] == 'dart' else \
                    "🏀" if game['game_type'] == 'basketball' else \
                    "⚽" if game['game_type'] == 'football' else \
                    "🎳" if game['game_type'] == 'bowling' else "🎰"
        
        result_emoji = "🎉" if game['type'] == 'win' else "😢"
        
        history_text += f"{i}. {game_emoji} <b>{game['game_type'].upper()}</b>\n"
        history_text += f"   👤 {game['first_name']} (@{game['username'] or 'нет'})\n"
        history_text += f"   💰 Ставка: {abs(game['amount'])} звезд\n"
        history_text += f"   🎯 Результат: {result_emoji} {'ВЫИГРЫШ' if game['type'] == 'win' else 'ПРОИГРЫШ'}\n"
        
        if game['type'] == 'win':
            history_text += f"   🏆 Выигрыш: {game['amount']} звезд\n"
        
        history_text += f"   ⏰ {game['created_at'].strftime('%H:%M:%S')}\n"
        history_text += "   ─────────────────────\n"
    
    await message.answer(history_text, parse_mode="HTML")

@router.callback_query(F.data == 'admin_add_promocode')
async def admin_add_promocode(callback:CallbackQuery, state:FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Доступ запрещен")
        return

    await callback.answer()
    await callback.message.edit_text('Введите название промокода 👇', reply_markup=kb.back_to_admin())

    await state.set_state(states.AddPromocode.name)

@router.message(states.AddPromocode.name, F.text)
async def proces_add_promo_name(message:Message, state:FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return

    await state.update_data(name=message.text) # Название

    await message.answer('Введите промокод 👇', reply_markup=kb.back_to_admin())

    await state.set_state(states.AddPromocode.code)

@router.message(states.AddPromocode.code, F.text)
async def proces_add_promo_code(message:Message, state:FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    await state.update_data(code=message.text) # Промокод

    await message.answer('Введите награду (только число звезд) 👇', reply_markup=kb.back_to_admin())

    await state.set_state(states.AddPromocode.reward)

@router.message(states.AddPromocode.reward, F.text)
async def proces_add_promo_reward(message:Message, state:FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    try:
        reward = int(message.text) # Награда
    except ValueError:
        await message.answer("❌ Введите целое число (количество звёзд)")
        return 

    await state.update_data(reward=reward)

    await message.answer('Введите дату окончания в формате \n<b>день.месяц.год часы:минуты</b>👇 \n\nЕсли промокод бессрочный напишите "-"', reply_markup=kb.back_to_admin())

    await state.set_state(states.AddPromocode.avaible_until)

@router.message(states.AddPromocode.avaible_until, F.text)
async def proces_add_promo_avaible_until(message:Message, state:FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    if message.text != '-':
        await state.update_data(avaible_until=message.text) # Если не "-" то дата
    else:
        await state.update_data(avaible_until=None) # Если "-" ничего

    add_promo_data = await state.get_data()

    msg = f'''✅ Подтвердите добавление промокода

    📋 Название: {add_promo_data.get('name')}
    🤝 Код: {add_promo_data.get('code')}
    💎 Награда: {add_promo_data.get('reward')}
    🕐 Окончание: {'Нет' if add_promo_data.get('avaible_until') == None else add_promo_data.get('avaible_until')}
'''
    await message.answer(msg, reply_markup=kb.approve_or_cancel())

    await state.set_state(states.AddPromocode.approve)

@router.callback_query(states.AddPromocode.approve, F.data.startswith('promo_'))
async def complete_promo(callback:CallbackQuery, state:FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        return
    
    data = callback.data.split('_')[1]
    promo_data = await state.get_data()

    name = promo_data.get('name')
    code = promo_data.get('code')
    reward = promo_data.get('reward')
    avaible_until = promo_data.get('avaible_until')


    if data == 'approve':
        try:
            await db.add_promo_to_db(name, code, reward, avaible_until)

            await callback.answer()
            await callback.message.edit_text('🎉 Промокод успешно добавлен', reply_markup=kb.back_to_admin())
            await state.clear()
        except ValueError as e:
            await callback.answer()
            await callback.message.answer(f'❌ Ошибка при создании промокода: {e}')

    if data == 'cancel':
        await admin_back(callback)
        await state.clear()

@router.callback_query(F.data == 'admin_promocodes')
async def show_promocodes(callback:CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    
    await callback.answer()
    await callback.message.edit_text('📋 Список всех промокодов', reply_markup=await kb.show_all_promocodes())

@router.callback_query(F.data.startswith('code_'))
async def code_info(callback:CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    
    code = callback.data.split('_')[1]
    code_info = await db.get_promocode_by_code(code)

    await callback.answer()
    await callback.message.edit_text(f'''📋 {code_info.name} | {code_info.code}

💎 Награда: {code_info.reward}
🚦 Состояние: {'✅ Включен' if code_info.is_available else '❌ Выключен'}
🕐 До: {code_info.available_until}

Выберите действие 👇
''', reply_markup=await kb.code_actions(code_info.id, code_info.is_available))
    
@router.callback_query(F.data.startswith('action_'))
async def actions_coddes(callback:CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    
    action = callback.data.split('_')[1]
    promo_id = callback.data.split('_')[2]

    if action == 'off':
        try:
            await db.switch_available_promo(promo_id)
            await callback.answer()
            await callback.message.answer('✅ Промокод успешно отключен')

        except ValueError as e:
            await callback.answer()
            await callback.message.answer(f'❌ Ошибка при отключении: {e}')

    if action == 'delete':
        try:
            await db.delete_promo(promo_id)
            await callback.answer()
            await callback.message.answer('✅ Промокод успешно удалён')

        except ValueError as e:
            await callback.answer()
            await callback.message.answer(f'❌ Ошибка при отключении: {e}')

    if action == 'admin_back':
        await admin_back(callback)

@router.callback_query(F.data == "admin_back")
async def admin_back(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    
    await callback.message.edit_text("👨‍💻 Панель администратора:", reply_markup=kb.admin_menu())

@router.callback_query(F.data == 'mass_message')
async def mass_message(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        return
    
    await callback.answer()
    await callback.message.answer('📣 Отправьте сообщение для рассылки (можно фото с подписью)')
    await state.set_state(states.MassMessage.message)

@router.message(states.MassMessage.message, F.text)
async def process_mass_message_text(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    await state.update_data(text=message.text, photo=None, caption=None)
    await show_mass_preview(message, state)

@router.message(states.MassMessage.message, F.photo)
async def process_mass_message_photo(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    photo = message.photo[-1]  # самое качественное фото
    file_id = photo.file_id
    caption = message.caption or ""
    await state.update_data(photo=file_id, caption=caption, text=None)
    await show_mass_preview(message, state)

async def show_mass_preview(message: Message, state: FSMContext):
    data = await state.get_data()
    text = data.get('text')
    photo = data.get('photo')
    caption = data.get('caption')

    if photo:
        # Предпросмотр с фото
        await message.answer_photo(
            photo=photo,
            caption=f"📣 <b>Предпросмотр рассылки</b>\n\n{caption}" if caption else "📣 <b>Предпросмотр рассылки</b>",
            parse_mode="HTML",
            reply_markup=kb.confirm_mass_message()
        )
    else:
        # Предпросмотр текста
        preview_text = f"📣 <b>Предпросмотр рассылки</b>\n\n{text or ''}"
        await message.answer(
            preview_text,
            parse_mode="HTML",
            reply_markup=kb.confirm_mass_message()
        )
    
    await state.set_state(states.MassMessage.confirm)

@router.callback_query(states.MassMessage.confirm, F.data.in_(["mass_approve", "mass_cancel"]))
async def process_mass_message_confirm(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        return
    
    await callback.answer()
    
    if callback.data == "mass_cancel":
        await callback.message.edit_text("❌ Рассылка отменена", reply_markup=kb.back_to_admin())
        await state.clear()
        return
    
    # Подтверждено – начинаем рассылку
    data = await state.get_data()
    text = data.get('text')
    photo = data.get('photo')
    caption = data.get('caption')
    
    if not text and not photo:
        await callback.message.answer("❌ Нет содержимого для рассылки", reply_markup=kb.back_to_admin())
        await state.clear()
        return
    
    users = await db.get_all_users()
    total = len(users)
    if total == 0:
        await callback.message.answer("📭 Нет пользователей для рассылки", reply_markup=kb.back_to_admin())
        await state.clear()
        return
    
    await callback.message.answer(f"⏳ Начинаю рассылку {total} пользователям...")
    
    sent = 0
    failed = 0
    
    for user in users:
        try:
            if photo:
                await bot.send_photo(chat_id=user.user_id, photo=photo, caption=caption or "", parse_mode="HTML")
            else:
                await bot.send_message(chat_id=user.user_id, text=text or "", parse_mode="HTML")
            sent += 1
        except Exception:
            failed += 1
        
        # Обновляем статус каждые 10 сообщений
        if (sent + failed) % 10 == 0:
            await callback.message.answer(
                f"⏳ Отправлено {sent + failed} из {total}... (успешно: {sent}, ошибок: {failed})"
            )
        await asyncio.sleep(0.05)  # задержка для соблюдения лимитов Telegram
    
    await callback.message.answer(
        f"✅ Рассылка завершена!\n\n"
        f"👥 Всего: {total}\n"
        f"✅ Доставлено: {sent}\n"
        f"❌ Ошибок: {failed}",
        reply_markup=kb.back_to_admin()
    )
    await state.clear()


@router.callback_query(F.data == 'send_gift')
async def send_gift_username(callback:CallbackQuery, state:FSMContext):
    await callback.answer()
    await callback.message.answer('👇 Введите @username пользователя')

    await state.set_state(states.SendGift.username)

@router.message(states.SendGift.username, F.text)
async def send_gift_text(message:Message, state:FSMContext):
    await state.update_data(username=message.text[1:])

    await message.answer('👇 Введите комментарий к подарку (или "-")')

    await state.set_state(states.SendGift.msg)

@router.message(states.SendGift.msg, F.text)
async def proces_send_gift(message:Message, state:FSMContext):
    await state.update_data(text = (message.text if message.text != '-' else None))
    gifts = await bot(GetAvailableGifts())

    await message.answer('👇 Выберите подарок для отправки', reply_markup= await kb.list_avaible_gifts(gifts.gifts))

@router.callback_query(F.data.startswith('admgift_'))
async def send_gift_from_user(callback:CallbackQuery, state:FSMContext):
    gift_id = callback.data.split('_')[1]

    data = await state.get_data()
    username = data.get('username')
    msg = data.get('msg')

    user_id = await db.get_user_by_username(username)

    await callback.answer()

    try:

        await bot.send_gift(
            user_id=int(user_id.user_id),
            gift_id=str(gift_id),  
            text=msg
        )

        await callback.message.answer(f'✅ Подарок успешно отправлен пользователю: @{username}')

    except Exception as e:
        await callback.message.answer(f'❌ Ошибка отправки подарка: {e}')