import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
from database import db

async def switch_available():
    """Проверяет все промокоды и деактивирует просроченные"""
    try:
        promocodes = await db.get_promocodes()
        now = datetime.now()

        for promo in promocodes:
            try:
                if promo.available_until:
                    # Парсим дату из строки (если храните как строку)
                    promo_datetime = datetime.strptime(promo.available_until, "%d.%m.%Y %H:%M") 
            except ValueError as e:
                logging.error(f"❌ Некорректный формат даты у промокода {promo.id}: {e}")
                continue  # пропускаем этот промокод

            if promo.available_until:
                # Проверяем, истёк ли срок и активен ли промокод
                if promo_datetime <= now and promo.is_available == 1:
                    try:
                        await db.switch_available_promo(promo.id)
                        logging.info(f"✅ Промокод {promo.id} деактивирован")
                    except Exception as e:
                        logging.error(f"❌ Ошибка деактивации промокода {promo.id}: {e}")

    except Exception as e:
        logging.error(f"❌ Критическая ошибка при получении списка промокодов: {e}")

async def switch_available_chat_game_status():
    all_chat_games = await db.get_all_chat_game()
    time_now = datetime.now()

    for game in all_chat_games:
        if game.created_at + timedelta(minutes=5) <= time_now and game.status == 'created':
            try:
                await db.update_chat_game_status(game.id, 'rejected')
                await db.add_stars_to_user_by_userid(game.creator, game.price, 'return', 'Отмена игры')
            except ValueError as e:
                logging.error(f'❌ Ошибка при обновлении статуса игры в чате: {e}')

# Создаём планировщик
scheduler = AsyncIOScheduler()

# Добавляем задачу – каждые 5 минут (в начале каждой 5-й минуты)
scheduler.add_job(
    switch_available,
    'cron',
    minute='*/5',
    id='switch_available_promo',
    next_run_time=datetime.now(),   # выполнить сразу при старте
    replace_existing=True
)


scheduler.add_job(
    switch_available_chat_game_status,
    'interval',
    minutes=1,
    id='switch_available_chat_game_status',
    next_run_time=datetime.now()
)