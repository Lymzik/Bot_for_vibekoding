from aiogram.fsm.state import State, StatesGroup


class TZStates(StatesGroup):
    goal = State()
    audience = State()
    features = State()
    constraints = State()
    result = State()
