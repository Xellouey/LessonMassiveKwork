import config
import utils
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def markup_admin(user_id):
    items = [
        [InlineKeyboardButton(text='📥 Рассылка', callback_data='mail')], 
        [InlineKeyboardButton(text='⬇️ Выгрузить пользователей', callback_data='export')], 
        [InlineKeyboardButton(text='✏️ Редактор шагов', callback_data='editor')] 
    ]
    
    if user_id in config.ADMINS:
        items.append([InlineKeyboardButton(text='🔑 Выдать / Забрать права администратора', callback_data='adminRights')]) 
    
    markup_admin = InlineKeyboardMarkup(inline_keyboard=items)
    return markup_admin


def markup_pass():
    items = [
        [KeyboardButton(text='➡️ Пропустить')]
        [KeyboardButton(text='❌ Отмена')]
    ]
    
    markup_pass = ReplyKeyboardMarkup(keyboard=items, resize_keyboard=True)
    return markup_pass


def markup_phone():
    items = [
        [KeyboardButton(text='📞 Авторизация', request_contact=True)]
    ]
    
    markup_phone = ReplyKeyboardMarkup(keyboard=items, resize_keyboard=True, one_time_keyboard=True)
    return markup_phone


def markup_cancel():
    items = [
        [KeyboardButton(text='❌ Отмена')]
    ]
    
    markup_cancel = ReplyKeyboardMarkup(keyboard=items, resize_keyboard=True)
    return markup_cancel


def markup_remove():
    markup_remove = ReplyKeyboardRemove()
    return markup_remove
    

def markup_pass():
    items = [
        [KeyboardButton(text='➡️ Пропустить')],
        [KeyboardButton(text='❌ Отмена')]
    ]
    
    markup_pass = ReplyKeyboardMarkup(keyboard=items, resize_keyboard=True)
    return markup_pass


def markup_confirm():
    items = [
        [KeyboardButton(text='✅ Да')],
        [KeyboardButton(text='❌ Отмена')]
    ]
    
    markup_confirm = ReplyKeyboardMarkup(keyboard=items, resize_keyboard=True)
    return markup_confirm


def markup_custom(keyboard):
    if keyboard == None:
        return None
    
    items = []

    for button in keyboard:
        for name in button:
            url = button[name]
            items.append([InlineKeyboardButton(text=name, url=url)])
        
    markup_custom = InlineKeyboardMarkup(inline_keyboard=items)
    return markup_custom


def markup_editor():
    items = [
        [
            InlineKeyboardButton(text='➕ Создать шаг', callback_data='createStep')
        ],
        [
            InlineKeyboardButton(text='🤝 Вступление', callback_data='edit:join'),
            InlineKeyboardButton(text='👋 Старт', callback_data='edit:start')
        ]
    ]
    
    steps = utils.get_steps()
    s_list = list(steps.keys())
    
    try:
        step_bot = s_list[2:]
    except:
        step_bot = []
        
    row = []
    
    i = 1
    for step in step_bot:
        row.append(InlineKeyboardButton(text=f"👟 Шаг{i}", callback_data=f"edit:{step}"))
        
        if len(row) == 2:
            items.append(row)
            row = []
            
        i += 1
            
    if row != []:
        items.append(row)
        
    items.append([InlineKeyboardButton(text='↪️ Назад', callback_data='backAdmin')])
    
    markup_editor = InlineKeyboardMarkup(inline_keyboard=items)
    return markup_editor


def markup_edit(disable_default=False):
    items = [
        [KeyboardButton(text='👟 Шаг')]
    ]
    
    if disable_default == False:
        items.extend((
            [
                KeyboardButton(text='🖌 Позицию'),
                KeyboardButton(text='⏳ Задержку')
            ],
            [
                KeyboardButton(text='🔗 Кнопки'),
                KeyboardButton(text='⛔️ Удалить')
            ]
        ))
        
    items.append([KeyboardButton(text='❌ Отмена')])
    
    markup_edit = ReplyKeyboardMarkup(keyboard=items, resize_keyboard=True)
    return markup_edit