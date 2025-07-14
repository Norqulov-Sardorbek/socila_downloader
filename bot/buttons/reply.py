from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from bot.models import *
from bot.buttons.text import *






def language_btn():
    keyboard1 = KeyboardButton(text=uz_text)
    keyboard2 = KeyboardButton(text=ru_text)
    design = [[keyboard1, keyboard2]]
    return ReplyKeyboardMarkup(keyboard=design, resize_keyboard=True)

def back_uz():
    keyboard1 = KeyboardButton(text = ortga)
    design = [[keyboard1]]
    return ReplyKeyboardMarkup(keyboard=design , resize_keyboard=True)
def back_ru():
    keyboard1 = KeyboardButton(text = nazad)
    design = [[keyboard1]]
    return ReplyKeyboardMarkup(keyboard=design , resize_keyboard=True)

def menu_back_uz():
    keyboard3=KeyboardButton(text=menuga_uz)
    design=[[keyboard3]]
    return ReplyKeyboardMarkup(keyboard=design, resize_keyboard=True)
def menu_back_ru():
    keyboard3=KeyboardButton(text=menuga_ru)
    design=[[keyboard3]]
    return ReplyKeyboardMarkup(keyboard=design, resize_keyboard=True)
