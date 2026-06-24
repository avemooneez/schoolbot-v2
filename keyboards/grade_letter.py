from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from utils.downloading_file import SendScheduleImage


def grade_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    for i in range(5, 12):
        kb.add(KeyboardButton(text=str(i)))
    kb.adjust(3)
    return kb.as_markup(resize_keyboard=True)


def letter_kb(grade) -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    match grade:
        case "5":
            for letter in ["А", "Б", "В", "Г", "Д", "Е", "Ж", "И"]:
                kb.add(KeyboardButton(text=letter))
        case "6":
            for letter in ["А", "Б", "В", "Г", "Д", "З", "Ж"]:
                kb.add(KeyboardButton(text=letter))
        case "7":
            for letter in ["А", "Б", "В", "Г", "Д", "Е"]:
                kb.add(KeyboardButton(text=letter))
        case "8":
            for letter in ["А", "Б", "В", "Г", "Д", "Е"]:
                kb.add(KeyboardButton(text=letter))
        case "9":
            for letter in ["А", "Б", "В", "Г", "Д", "Е"]:
                kb.add(KeyboardButton(text=letter))
        case "10":
            for letter in ["А", "Б"]:
                kb.add(KeyboardButton(text=letter))
        case "11":
            for letter in ["А"]:
                kb.add(KeyboardButton(text=letter))
    return kb.as_markup(resize_keyboard=True)


def isAllCorrect_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.add(KeyboardButton(text="Всё верно"))
    kb.add(KeyboardButton(text="Нет, изменить"))
    return kb.as_markup(resize_keyboard=True)
