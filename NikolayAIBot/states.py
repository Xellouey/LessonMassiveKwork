from aiogram.fsm.state import State, StatesGroup


class FSMMail(StatesGroup):
    date_mail = State()
    message = State()
    keyboard = State()
    confirm = State()
    
    
class FSMAdminRights(StatesGroup):
    user = State()
    
    
class FSMEditor(StatesGroup):
    action = State()
    value = State()
    
    
class FSMCreateStep(StatesGroup):
    step = State()
    
# class FSMSuperPower(StatesGroup):
    # birthdate = State()