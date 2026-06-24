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

class Grades(StatesGroup):
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
    await state.set_state(Grades.letter)


async def handle_letter_selection(message: Message, state: FSMContext):
    """Обработка выбора буквы класса."""
    letter = message.text.strip().upper()
    user_data = await state.get_data()
    grade = user_data.get("grade")

    # допустимые буквы по классам
    valid_letters = {
        "5": ["А", "Б", "В", "Г", "Д", "Е", "Ж", "И"],
        "6": ["А", "Б", "В", "Г", "Д", "З", "Ж"],
        "7": ["А", "Б", "В", "Г", "Д", "Е"],
        "8": ["А", "Б", "В", "Г", "Д", "Е"],
        "9": ["А", "Б", "В", "Г", "Д", "Е"],
        "10": ["А", "Б"],
        "11": ["А"],
    }

    # проверяем, что введённая буква допустима для данного класса
    if grade not in valid_letters or letter not in valid_letters[grade]:
        await message.answer(
            "Пожалуйста, выберите букву класса из предложенных вариантов.",
            reply_markup=grade_letter.letter_kb(grade=grade),
        )
        return

    await state.update_data(letter=letter)

    await message.answer(
        f"Вы в {grade}{letter} классе. Всё верно?",
        reply_markup=grade_letter.isAllCorrect_kb(),
    )
    await state.set_state(Grades.isAllCorrect)


async def handle_confirmation(message: Message, state: FSMContext, db: Database, schedule: SendScheduleImage, is_new_user: bool):
    """Обработка подтверждения выбора класса."""
    if message.text == "Всё верно":
        gradeLetter = await state.get_data()
        try:
            grade = int(gradeLetter['grade'])
            letter = str(gradeLetter['letter'])
            
            if is_new_user:
                db.add_user(message.from_user.id, grade, letter)
            else:
                db.update_user(message.from_user.id, grade, letter)
            
            await message.answer("Отлично!", reply_markup=ReplyKeyboardRemove())
            await schedule.send_schedule_images_for_one(message, db, message.from_user.id)
        except ValueError as e:
            logging.error(f"Ошибка валидации данных: {e}")
            await message.answer("Произошла ошибка при обработке данных. Попробуйте позже.")
        except Exception as e:
            logging.error(f"Ошибка при сохранении данных пользователя: {e}")
            await message.answer("Произошла ошибка. Попробуйте позже.")
        finally:
            await state.clear()
    else:
        await message.answer(
            "Начинаем заново. Выберите ваш класс в клавиатуре ниже.",
            reply_markup=grade_letter.grade_kb()
        )
        await state.clear()
        await state.set_state(Grades.grade)


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext, db: Database, schedule: SendScheduleImage):
    """Обработчик команды /start."""
    if not db.user_exists(message.from_user.id):
        await message.answer(
            "Вы новый пользователь! Выберите ваш класс в клавиатуре ниже.",
            reply_markup=grade_letter.grade_kb()
        )
        await state.set_state(Grades.grade)
        return
    await message.answer(
        "Добро пожаловать в бота! Это — бот с расписанием уроков в школе №9.",
        reply_markup=ReplyKeyboardRemove()
    )


@router.message(Grades.grade)
async def grade_handler(message: Message, state: FSMContext):
    """Обработчик выбора класса."""
    await handle_grade_selection(message, state)


@router.message(Grades.letter)
async def letter_handler(message: Message, state: FSMContext):
    """Обработчик выбора буквы класса."""
    await handle_letter_selection(message, state)


@router.message(Grades.isAllCorrect)
async def isAllCorrect_handler(message: Message, state: FSMContext, db: Database, schedule: SendScheduleImage):
    """Обработчик подтверждения выбора класса."""
    await handle_confirmation(message, state, db, schedule, is_new_user=True)
