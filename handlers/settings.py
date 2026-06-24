from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards import grade_letter
from db import Database
from utils.downloading_file import SendScheduleImage
import logging

router = Router()

class SettingsGrades(StatesGroup):
    grade = State()
    letter = State()
    isAllCorrect = State()


async def handle_grade_selection(message: Message, state: FSMContext):
    """Обработка выбора класса."""
    grade = message.text
    if not grade.isdigit() or not (5 <= int(grade) <= 11):
        await message.answer("Пожалуйста, выберите класс из предложенных вариантов.")
        return
    
    await state.update_data(grade=grade)
    await message.answer(
        f"Вы выбрали класс {grade}. Выберите букву класса ниже.",
        reply_markup=grade_letter.letter_kb(grade=grade)
    )
    await state.set_state(SettingsGrades.letter)


async def handle_letter_selection(message: Message, state: FSMContext):
    """Обработка выбора буквы класса."""
    letter = message.text
    await state.update_data(letter=letter)
    gradeLetter = await state.get_data()
    await message.answer(
        f"Вы в {gradeLetter['grade']}{gradeLetter['letter']} классе. Всё верно?",
        reply_markup=grade_letter.isAllCorrect_kb()
    )
    await state.set_state(SettingsGrades.isAllCorrect)


async def handle_confirmation(message: Message, state: FSMContext, db: Database, schedule: SendScheduleImage):
    """Обработка подтверждения изменения настроек."""
    if message.text == "Всё верно":
        gradeLetter = await state.get_data()
        try:
            grade = int(gradeLetter['grade'])
            letter = str(gradeLetter['letter'])
            
            db.update_user(message.from_user.id, grade, letter)
            await message.answer("Отлично!", reply_markup=ReplyKeyboardRemove())
            await schedule.send_schedule_images_for_one(message, db, message.from_user.id)
        except ValueError as e:
            logging.error(f"Ошибка валидации данных: {e}")
            await message.answer("Произошла ошибка при обработке данных. Попробуйте позже.")
        except Exception as e:
            logging.error(f"Ошибка при обновлении пользователя: {e}")
            await message.answer("Произошла ошибка. Попробуйте позже.")
        finally:
            await state.clear()
    else:
        await message.answer(
            "Начинаем заново. Выберите ваш класс в клавиатуре ниже.",
            reply_markup=grade_letter.grade_kb()
        )
        await state.clear()
        await state.set_state(SettingsGrades.grade)


@router.message(Command("settings"))
async def cmd_settings(message: Message, state: FSMContext):
    """Обработчик команды /settings."""
    await message.answer(
        "Выберите Ваш класс в клавиатуре ниже.",
        reply_markup=grade_letter.grade_kb()
    )
    await state.set_state(SettingsGrades.grade)


@router.message(SettingsGrades.grade)
async def grade_handler(message: Message, state: FSMContext):
    """Обработчик выбора класса."""
    await handle_grade_selection(message, state)


@router.message(SettingsGrades.letter)
async def letter_handler(message: Message, state: FSMContext):
    """Обработчик выбора буквы класса."""
    await handle_letter_selection(message, state)


@router.message(SettingsGrades.isAllCorrect)
async def isAllCorrect_handler(message: Message, state: FSMContext, db: Database, schedule: SendScheduleImage):
    """Обработчик подтверждения изменения настроек."""
    await handle_confirmation(message, state, db, schedule)