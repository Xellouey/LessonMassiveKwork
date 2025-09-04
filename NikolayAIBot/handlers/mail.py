import asyncio
import config
import json
import logging
import keyboards as kb
from datetime import datetime as dt
from aiogram import types, Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from states import FSMMail
from database import mail


logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(name)s - %(filename)s - %(message)s",
    # filename='file.log'
)

router = Router()
bot = Bot(config.TOKEN)
m = mail.Mail()


@router.callback_query(F.data == 'mail')
async def mailingFirstLine(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(FSMMail.date_mail)
    
    await call.message.answer('👉 Отправьте время в формате дд.мм.гггг чч:мм или нажмите кнопку ➡️ Пропустить', reply_markup=kb.markup_pass())
    await call.answer()
    
    
@router.message(FSMMail.date_mail)
async def takeMailDatetime(message: types.Message, state: FSMMail):
    if message.text == '➡️ Пропустить':
        date_mail = dt.now()
    else:
        try:
            date_mail = dt.strptime(message.text, '%d.%m.%Y %H:%M')
        except:
            await message.answer('👉 Отправьте корректное время в формате дд.мм.гггг чч:мм или нажмите кнопку ➡️ Пропустить', reply_markup=kb.markup_pass())
            return 
        
    await state.update_data(date_mail=date_mail)
    await state.set_state(FSMMail.message)
    
    await message.answer('👉 Отправьте ваше сообщение:', reply_markup=kb.markup_cancel())

    
@router.message(FSMMail.message)
async def takeMailMessage(message: types.Message, state: FSMMail):
    message_id = message.message_id
    from_id = message.from_user.id
    
    await state.update_data(message_id=message_id, from_id=from_id)
    await state.set_state(FSMMail.keyboard)
    
    await message.answer('👉 Хотите ли вы добавить клавиатуру? Нажмите ➡️ Пропустить или впишите клавиатуру в формате JSON: [{"Название": "ссылка"}, {"Название": "ссылка"}], например <code>[{"Google": "google.com"}, {"Yandex": "yandex.ru"}]</code>', parse_mode='html', reply_markup=kb.markup_pass())
  
    
@router.message(FSMMail.keyboard)
async def takeMailkeyboard(message: types.Message, state: FSMMail):    
    if message.text.lower() == '➡️ пропустить':
        keyboard = None
        
    else:
        keyboard = message.text

        try:
            keyboard = json.loads(keyboard)
        except:
            await message.answer('👉 Хотите ли вы добавить клавиатуру? Нажмите ➡️ Пропустить или впишите клавиатуру в формате JSON: [{"Название": "ссылка"}, {"Название": "ссылка"}], например <code>[{"Google": "google.com"}, {"Yandex": "yandex.ru"}]</code>', parse_mode='html', reply_markup=kb.markup_pass())
            return

    await state.update_data(keyboard=keyboard)
    await state.set_state(FSMMail.confirm)
    
    stateData = await state.get_data()
    message_id = stateData['message_id']
    from_id = stateData['from_id']
    
    await bot.copy_message(message.from_user.id, from_id, message_id, reply_markup=kb.markup_custom(keyboard))
    await message.answer('👉 Вы уверены, что хотите разослать это сообщение?', reply_markup=kb.markup_confirm())
    
    
@router.message(FSMMail.confirm)
async def takeMailConfirm(message: types.Message, state: FSMMail):
    try:
        if message.text.lower() != '✅ да':
            await message.answer('👉 Вы уверены, что хотите разослать это сообщение?', reply_markup=kb.markup_confirm())
            return
    except:
        await message.answer('👉 Вы уверены, что хотите разослать это сообщение?', reply_markup=kb.markup_confirm())
        return

    stateData = await state.get_data()
    date_mail = stateData['date_mail']
    message_id = stateData['message_id']
    from_id = stateData['from_id']
    keyboard = stateData['keyboard']
    await state.clear()

    date_mail_str = date_mail.strftime('%d.%m.%Y %H:%M')

    await m.create_mail(date_mail, message_id, from_id, keyboard)
    await message.answer(f'✅ Рассылка будет запущена {date_mail_str}', reply_markup=kb.markup_remove())
