from aiogram.types import Message
from aiogram.filters import Command
from aiogram import Router
from db import Database
import logging

router = Router()


def get_admin_ids(db: Database) -> set:
    """Получает множество ID администраторов из базы данных."""
    admins = db.get_admins()
    return {admin[0] for admin in admins} if admins else set()


@router.message(Command("send_msg"))
async def cmd_send_msg(message: Message, db: Database):
    """Отправляет сообщение всем активным пользователям. Только для администраторов."""
    try:
        # Проверка прав администратора
        admin_ids = get_admin_ids(db)
        if message.from_user.id not in admin_ids:
            await message.answer("Вы не админ.")
            return

        # Проверка наличия текста сообщения
        if len(message.text) <= 10:
            await message.answer(
                "Сообщение слишком короткое. Используйте: /send_msg ваш текст"
            )
            return

        message_text = message.text[10:].strip()
        if not message_text:
            await message.answer("Текст сообщения не может быть пустым.")
            return

        # Отправка сообщения всем активным пользователям
        users = db.get_active_users()
        success_count = 0
        error_count = 0

        for user in users:
            try:
                await message.bot.send_message(chat_id=user[0], text=message_text)
                success_count += 1
            except Exception as e:
                error_count += 1
                logging.warning(
                    f"Не удалось отправить сообщение пользователю {user[0]}: {e}"
                )

        await message.answer(
            f"Сообщение отправлено.\n"
            f"Успешно: {success_count}\n"
            f"Ошибок: {error_count}"
        )
        logging.info(
            f"Сообщение отправлено {success_count} пользователям, ошибок: {error_count}"
        )
    except Exception as e:
        logging.error(f"Ошибка при отправке сообщения: {e}")
        await message.answer("Произошла ошибка при отправке сообщения.")
