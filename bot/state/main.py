from aiogram.fsm.state import StatesGroup, State


class MenuState(StatesGroup):
    menu = State()

class Subscribe(StatesGroup):
    subscribe = State()
