import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Update
from typing import Callable, Dict, Any
from utils import tokens
from handlers import start, settings, send_schedule, admin
from db import Database
from utils.downloading_file import SendScheduleImage
import os

for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Глобальные экземпляры (создаются один раз)
db = Database()
schedule = SendScheduleImage()


def create_database_middleware(db_instance: Database):
    """Создает middleware для передачи экземпляра Database в handlers."""
    async def middleware(handler: Callable, event: Update, data: Dict[str, Any]) -> Any:
        data['db'] = db_instance
        return await handler(event, data)
    return middleware


def create_schedule_middleware(schedule_instance: SendScheduleImage):
    """Создает middleware для передачи экземпляра SendScheduleImage в handlers."""
    async def middleware(handler: Callable, event: Update, data: Dict[str, Any]) -> Any:
        data['schedule'] = schedule_instance
        return await handler(event, data)
    return middleware


async def schedule_start():
    """Асинхронная функция для скачивания расписания."""
    try:
        await schedule.download_file(output_file=schedule.file_name)
        logging.info("Расписание успешно скачано")
    except Exception as e:
        logging.error(f"Ошибка при скачивании расписания: {e}")


async def main():
    """Главная функция запуска бота."""
    # Сброс старых обработчиков логов, чтобы INFO точно отображался
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    try:
        db.start()
    except Exception as e:
        logging.error(f"Ошибка при инициализации базы данных: {e}")
        return
    
    bot = Bot(token=tokens.bot_token)
    dp = Dispatcher()

    # Добавляем middleware
    dp.message.middleware(create_database_middleware(db))
    dp.message.middleware(create_schedule_middleware(schedule))

    dp.include_routers(
        start.router,
        settings.router,
        send_schedule.router,
        admin.router,
    )

    dp.message.filter(F.chat.type.in_({"private"}))
    
    try:
        await bot.delete_webhook(drop_pending_updates=True)
    except Exception as e:
        logging.error(f"Ошибка при удалении webhook: {e}")

    # Скачиваем расписание при первом запуске
    if not os.path.exists('temp/schedule.docx'):
        await schedule_start()

    logging.info("Бот запускается...")

    try:
        # ✅ Здесь заменяем gather на TaskGroup
        async with asyncio.TaskGroup() as tg:
            tg.create_task(dp.start_polling(bot))
            tg.create_task(schedule.check_new_schedule(bot=bot, db=db))
    except* KeyboardInterrupt:
        logging.info("Остановка по Ctrl+C...")
    except* Exception as e:
        logging.error(f"Критическая ошибка: {e}")
    finally:
        await bot.session.close()
        db.close()
        logging.info("Бот остановлен")


if __name__ == "__main__":
    asyncio.run(main())
