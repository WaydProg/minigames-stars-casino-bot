import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
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