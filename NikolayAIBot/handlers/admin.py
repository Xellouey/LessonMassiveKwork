import config
import logging
import utils
import os
import json
import keyboards as kb
import pandas as pd
from .client import send_msg
from database import user
from datetime import datetime
from aiogram import Bot, types, Router, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from states import FSMAdminRights, FSMEditor, FSMCreateStep

logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(name)s - %(filename)s - %(message)s",
)


bot = Bot(config.TOKEN)
router = Router()
u = user.User()


@router.message(Command('admin'))
async def admin(message: types.Message, state: FSMContext):
    data_admins = utils.get_admins()
    
    if await state.get_state() != None:
        await state.clear()

    if message.from_user.id not in config.ADMINS and message.from_user.id not in data_admins:
        await message.answer('⚠️ Ошибка доступа')    
        return
    
    if message.from_user.id in config.ADMINS:
        text_rights = "Вы обладаете всеми правами главного администратора! 🔑"
    elif message.from_user.id in data_admins:
        text_rights = "Вы обладаете правами администратора! 🔑"
        
    await message.answer(f"""
## Добро пожаловать, Администратор! 👽

Ваше имя: <b>{message.from_user.full_name}</b>
ID пользователя: <b>{message.from_user.id}</b>

{text_rights}
""", parse_mode='html', reply_markup=kb.markup_admin(message.from_user.id))
    
    
@router.callback_query(F.data == 'backAdmin')
async def backAdmin(call: types.CallbackQuery, state: FSMContext):
    data_admins = utils.get_admins()

    if call.from_user.id not in config.ADMINS and call.from_user.id not in data_admins:
        await call.answer()
        await call.message.answer('⚠️ Ошибка доступа')    
        return
    
    if call.from_user.id in config.ADMINS:
        text_rights = "Вы обладаете всеми правами главного администратора! 🔑"
    elif call.from_user.id in data_admins:
        text_rights = "Вы обладаете правами администратора! 🔑"
        
    await call.answer()
    await call.message.edit_text(f"""
## Добро пожаловать, Администратор! 👽

Ваше имя: <b>{call.from_user.full_name}</b>
ID пользователя: <b>{call.from_user.id}</b>

{text_rights}
""", parse_mode='html', reply_markup=kb.markup_admin(call.from_user.id))


@router.callback_query(F.data == 'export')
async def export(call: types.CallbackQuery, state: FSMContext):
    data_admins = utils.get_admins()
    
    if call.from_user.id not in config.ADMINS and call.from_user.id not in data_admins:
        await call.answer()
        await call.message.answer('⚠️ Ошибка доступа')
        return
    
    await call.answer()
    
    date_now = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
    
    name = f'Пользователи_{date_now}.xlsx'
    file_path = f'./{name}'
    
    users = await u.get_all_users()
    df = pd.DataFrame(users)
    # df = df.rename(columns={'user_id': 'newName1', 'oldName2': 'newName2'})
    df.to_excel(f'{file_path}', index=True)
    
    try:
        await call.message.answer_document(types.FSInputFile(file_path, filename=name))
    except:
        pass
    finally:
        os.remove(file_path)
        

@router.message(F.text.lower() == '❌ отмена')
async def cancel(message: types.Message, state: FSMContext):
    if await state.get_state() != None:
        await state.clear()
        
    data_admins = utils.get_admins()

    if message.from_user.id in config.ADMINS or message.from_user.id in data_admins:    
        await message.answer('❌ Отменено', reply_markup=kb.markup_remove())
        await admin(message, state)
    
    
@router.callback_query(F.data == 'adminRights')
async def adminRights(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(FSMAdminRights.user)
    
    await call.answer()
    await call.message.answer("👉 Введите ID пользователя:", reply_markup=kb.markup_cancel())
    
    
@router.message(FSMAdminRights.user)
async def userAdminRights(message: types.Message, state: FSMAdminRights):
    data_admins = utils.get_admins()
    
    user = message.text
    if user.isdigit():
        user_id = int(user)
        
        if user_id not in data_admins:
            data_admins.append(user_id)
            await message.answer(f"✅ Пользовать ID: <code>{user}</code> успешно <b>добавлен</b>", parse_mode='html', reply_markup=kb.markup_remove())
        elif user_id in data_admins:
            data_admins.remove(user_id)
            await message.answer(f"✅ Пользовать ID: <code>{user}</code> успешно <b>удален</b>", parse_mode='html', reply_markup=kb.markup_remove())
            
        utils.update_admins(data_admins)
        return
    
    else:
        await message.answer("👉 Введите корректный ID пользователя:", reply_markup=kb.markup_cancel())
        return
    
    
@router.callback_query(F.data == 'editor')
async def editor(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.edit_text("👉 Выберите шаг, который вы хотите отредактировать", parse_mode='html', reply_markup=kb.markup_editor())
    
    
@router.callback_query(lambda F: 'edit:' in F.data)
async def edit(call: types.CallbackQuery, state: FSMContext):
    key = call.data.split(':')[1]
    
    await state.set_state(FSMEditor.action)
    await state.update_data(key=key)
    
    steps = utils.get_steps()
    step = steps[key]
    
    await send_msg(step, call.message, None)
    
    if key in ('join', 'start'):
        disable_default = True
    else:
        disable_default = False
    
    await call.answer()
    await call.message.delete()
    await call.message.answer('👉 Что вы хотите изменить:', reply_markup=kb.markup_edit(disable_default=disable_default))
    

@router.message(FSMEditor.action)
async def actionEditor(message: types.Message, state: FSMEditor):
    action = message.text
    
    await state.set_state(FSMEditor.value)
    
    if action == '👟 Шаг':
        await state.update_data(action='step')
        await message.answer('👉 Отправьте новое сообщение:', reply_markup=kb.markup_cancel())
    
    elif action == '🖌 Позицию':
        await state.update_data(action='position')
        await message.answer('👉 Отправьте новую позицию для переноса шага:', reply_markup=kb.markup_cancel())
    
    elif action == '⏳ Задержку':
        await state.update_data(action='delay')
        await message.answer('👉 Отправьте новую задержку для шага:', reply_markup=kb.markup_pass())
    
    elif action == '🔗 Кнопки':
        await state.update_data(action='keyboard')
        await message.answer('👉 Отправьте новые кнопки для шага в формате JSON: [{"Название": "ссылка"}, {"Название": "ссылка"}], например <code>[{"Google": "google.com"}, {"Yandex": "yandex.ru"}]</code>', reply_markup=kb.markup_pass())
    
    elif action == '⛔️ Удалить':
        await state.update_data(action='delete')
        await message.answer('👉 Отправьте слово <code>Подтвердить</code> для удаления шага:', reply_markup=kb.markup_cancel())
    
    
@router.message(FSMEditor.value)
async def msgEditor(message: types.Message, state: FSMEditor):
    if message.content_type not in ('text', 'document', 'photo', 'video', 'audio', 'video_note', 'voice'):
        await message.answer('👉 Отправьте новое корректное сообщение:', reply_markup=kb.markup_cancel())
        return
    
    state_data = await state.get_data()
    key = state_data['key']
    action = state_data['action']
    await state.clear()
    
    steps = utils.get_steps()
    
    if action == 'step':
        content_type = message.content_type
        text = message.text
        caption = message.caption  
    
        if content_type != 'text':
            if message.caption_entities != None:
                custom_entities = []
                for entity in message.caption_entities:
                    if entity.type == 'custom_emoji':
                        continue
                    if entity.custom_emoji_id != None:
                        continue
                    
                    custom_entities.append(types.MessageEntity(type=entity.type, offset=entity.offset, length=entity.length, url=entity.url, user=entity.user, language=entity.user))
                    
                msg_caption = await message.answer(text=caption, entities=custom_entities, parse_mode=None)
                await msg_caption.delete()
                caption = msg_caption.html_text
            
        if content_type == 'photo':
            file_id = message.photo[-1].file_id
        elif content_type == 'document':
            file_id = message.document.file_id
        elif content_type == 'video':
            file_id = message.video.file_id
        elif content_type == 'audio':
            file_id = message.audio.file_id
        elif content_type == 'video_note':
            file_id = message.video_note.file_id
        elif content_type == 'voice':
            file_id = message.voice.file_id
        else:
            file_id = None
        
        steps[key]["content_type"] = content_type
        steps[key]["text"] = text
        steps[key]["caption"] = caption
        steps[key]["file_id"] = file_id
        utils.update_steps(steps)
        
        await message.answer('✅ Шаг успешно обновлен', reply_markup=kb.markup_remove())
        await message.answer("👉 Выберите шаг, который вы хотите отредактировать", parse_mode='html', reply_markup=kb.markup_editor())
        
    elif action == 'position':
        position = message.text
        
        try:
            position = int(position)
            if position < 1:
                raise
        except:
            await message.answer('👉 Отправьте новую корректную позицию:', reply_markup=kb.markup_cancel())
            return
        
        new_steps = utils.move_dict_item(steps, key, position + 1)
        utils.update_steps(new_steps)
        
        await message.answer('✅ Позиция шага успешно изменена', reply_markup=kb.markup_remove())
        await message.answer("👉 Выберите шаг, который вы хотите отредактировать", parse_mode='html', reply_markup=kb.markup_editor())
    
    elif action == 'delay':
        delay = message.text
        
        if delay.lower() == '➡️ пропустить':
            delay = 0
        else:
            try:
                delay = int(delay)
                if delay < 1:
                    raise
            except:
                await message.answer('👉 Отправьте новую корректную задержку:', reply_markup=kb.markup_cancel())
                return
            
        steps[key]['delay'] = delay
        utils.update_steps(steps)
        
        await message.answer('✅ Задержка шага успешно изменена', reply_markup=kb.markup_remove())
        await message.answer("👉 Выберите шаг, который вы хотите отредактировать", parse_mode='html', reply_markup=kb.markup_editor())
    
    elif action == 'keyboard':
        keyboard = message.text

        if message.text.lower() == '➡️ пропустить':
            keyboard = None
        else:
            keyboard = message.text

            try:
                keyboard = json.loads(keyboard)
            except:
                await message.answer('👉 Отправьте корректные кнопки для шага в формате JSON: [{"Название": "ссылка"}, {"Название": "ссылка"}], например <code>[{"Google": "google.com"}, {"Yandex": "yandex.ru"}]</code>', parse_mode='html', reply_markup=kb.markup_pass())
                return
            
        steps[key]['keyboard'] = keyboard
        utils.update_steps(steps)
        
        await message.answer('✅ Кнопки шага успешно изменены', reply_markup=kb.markup_remove())
        await message.answer("👉 Выберите шаг, который вы хотите отредактировать", parse_mode='html', reply_markup=kb.markup_editor())
    
    elif action == 'delete':
        if message.text != 'Подтвердить':
            await message.answer('👉 Отправьте слово <code>Подтвердить</code> для удаления шага:', reply_markup=kb.markup_cancel())
            return
        
        new_steps = utils.remove_dict_item(steps, key)
        utils.update_steps(new_steps)
        
        await message.answer('✅ Шаг успешно удалён', reply_markup=kb.markup_remove())
        await message.answer("👉 Выберите шаг, который вы хотите отредактировать", parse_mode='html', reply_markup=kb.markup_editor())
    
    
@router.callback_query(F.data == 'createStep')
async def createStep(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(FSMCreateStep.step)
    
    await call.answer()
    await call.message.answer('👉 Отправьте сообщение для нового шага:', reply_markup=kb.markup_cancel())
    
    
@router.message(FSMCreateStep.step)
async def stepCreate(message: types.Message, state: FSMCreateStep):
    steps = utils.get_steps()
    
    content_type = message.content_type
    text = message.text
    caption = message.caption  

    if content_type != 'text':
        if message.caption_entities != None:
            custom_entities = []
            for entity in message.caption_entities:
                if entity.type == 'custom_emoji':
                    continue
                if entity.custom_emoji_id != None:
                    continue
                
                custom_entities.append(types.MessageEntity(type=entity.type, offset=entity.offset, length=entity.length, url=entity.url, user=entity.user, language=entity.user))
                
            msg_caption = await message.answer(text=caption, entities=custom_entities, parse_mode=None)
            await msg_caption.delete()
            caption = msg_caption.html_text
        
    if content_type == 'photo':
        file_id = message.photo[-1].file_id
    elif content_type == 'document':
        file_id = message.document.file_id
    elif content_type == 'video':
        file_id = message.video.file_id
    elif content_type == 'audio':
        file_id = message.audio.file_id
    elif content_type == 'video_note':
        file_id = message.video_note.file_id
    elif content_type == 'voice':
        file_id = message.voice.file_id
    else:
        file_id = None
    
    key = utils.get_new_key()
    steps.update({
        key: {
            "content_type": content_type,
            "text": text,
            "caption": caption,
            "file_id": file_id,
            "keyboard": None,
            "delay": 0
        }
    })
    utils.update_steps(steps)
    
    await message.answer('✅ Шаг успешно добавлен', reply_markup=kb.markup_remove())
    await message.answer("👉 Выберите шаг, который вы хотите отредактировать", parse_mode='html', reply_markup=kb.markup_editor())