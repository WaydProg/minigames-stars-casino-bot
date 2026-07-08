from aiogram.fsm.state import StatesGroup, State

class AddPromocode(StatesGroup):
    name = State()
    code = State()
    reward = State()
    avaible_until = State()
    approve = State()

class ActivatePromocode(StatesGroup):
    code = State()