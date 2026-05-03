from aiogram.fsm.state import State, StatesGroup


class DeployStates(StatesGroup):
    project_type = State()
    code_input = State()
    awaiting_result = State()
