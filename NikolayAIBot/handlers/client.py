import asyncio
import utils
import logging
import keyboards as kb
from aiogram import types, Router, F, Bot
from database import user
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext


logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(name)s - %(filename)s - %(message)s",
    # filename='file.log'
)

u = user.User()
router = Router()


async def send_msg(data, message, keyboard=None, bot: Bot = None):
    content_type = data['content_type']
    text = data['text']
    caption = data['caption']
    file_id = data['file_id']

    async def send_message(chat_id, text, **kwargs):
        if type(message) != int:
            await message.answer(text, **kwargs)
        else:
            await bot.send_message(chat_id, text=text, **kwargs)

    async def send_document(chat_id, document, caption=None, **kwargs):
        if type(message) != int:
            await message.answer_document(document=document, caption=caption, **kwargs)
        else:
            await bot.send_document(chat_id, document=document, caption=caption, **kwargs)

    async def send_video(chat_id, video, caption=None, **kwargs):
        if type(message) != int:
            await message.answer_video(video=video, caption=caption, **kwargs)
        else:
            await bot.send_video(chat_id, video=video, caption=caption, **kwargs)

    async def send_photo(chat_id, photo, caption=None, **kwargs):
        if type(message) != int:
            await message.answer_photo(photo=photo, caption=caption, **kwargs)
        else:
            await bot.send_photo(chat_id, photo=photo, caption=caption, **kwargs)

    async def send_audio(chat_id, audio, caption=None, **kwargs):
        if type(message) != int:
            await message.answer_audio(audio=audio, caption=caption, **kwargs)
        else:
            await bot.send_audio(chat_id, audio=audio, caption=caption, **kwargs)

    async def send_video_note(chat_id, video_note, **kwargs):
        if type(message) != int:
            await message.answer_video_note(video_note=video_note, **kwargs)
        else:
            await bot.send_video_note(chat_id, video_note=video_note, **kwargs)

    async def send_voice(chat_id, voice, caption=None, **kwargs):
        if type(message) != int:
            await message.answer_voice(voice=voice, caption=caption, **kwargs)
        else:
            await bot.send_voice(chat_id, voice=voice, caption=caption, **kwargs)

    chat_id = message if type(message) == int else message.chat.id

    if content_type == 'text':
        await send_message(chat_id, text, parse_mode='html', disable_web_page_preview=True, reply_markup=keyboard)

    elif content_type == 'document':
        if caption and len(caption) > 1024:
            await send_document(chat_id, document=file_id)
            await send_message(chat_id, text=caption, parse_mode='html', disable_web_page_preview=True, reply_markup=keyboard)
        else:
            await send_document(chat_id, document=file_id, caption=caption, parse_mode='html', reply_markup=keyboard)

    elif content_type == 'video':
        if caption and len(caption) > 1024:
            await send_video(chat_id, video=file_id)
            await send_message(chat_id, text=caption, parse_mode='html', disable_web_page_preview=True, reply_markup=keyboard)
        else:
            await send_video(chat_id, video=file_id, caption=caption, parse_mode='html', reply_markup=keyboard)

    elif content_type == 'photo':
        if caption and len(caption) > 1024:
            await send_photo(chat_id, photo=file_id)
            await send_message(chat_id, text=caption, parse_mode='html', disable_web_page_preview=True, reply_markup=keyboard)
        else:
            await send_photo(chat_id, photo=file_id, caption=caption, parse_mode='html', reply_markup=keyboard)

    elif content_type == 'audio':
        if caption and len(caption) > 1024:
            await send_audio(chat_id, audio=file_id)
            await send_message(chat_id, text=caption, parse_mode='html', disable_web_page_preview=True, reply_markup=keyboard)
        else:
            await send_audio(chat_id, audio=file_id, caption=caption, parse_mode='html', reply_markup=keyboard)

    elif content_type == 'video_note':
        if caption and len(caption) > 1024:
            await send_video_note(chat_id, video_note=file_id)
            await send_message(chat_id, text=caption, parse_mode='html', disable_web_page_preview=True, reply_markup=keyboard)
        else:
            await send_video_note(chat_id, video_note=file_id, reply_markup=keyboard)

    elif content_type == 'voice':
        if caption and len(caption) > 1024:
            await send_voice(chat_id, voice=file_id)
            await send_message(chat_id, text=caption, parse_mode='html', disable_web_page_preview=True, reply_markup=keyboard)
        else:
            await send_voice(chat_id, voice=file_id, caption=caption, parse_mode='html', reply_markup=keyboard)
            
            
async def start_steps(message: types.Message, state: FSMContext):
    steps = utils.get_steps()
    steps_list = list(steps.values())
    
    try:
        step_bot = steps_list[2:]
    except:
        step_bot = []
        
    removed = False    
    
    i = 1
    for step in step_bot:
        keyboard = step['keyboard']
        delay = step['delay']
        markup = kb.markup_custom(keyboard)
        
        if markup == None and removed == False:
            markup = kb.markup_remove()
            removed = True
        
        await send_msg(step, message, markup)
        
        if i != len(step_bot):
            await asyncio.sleep(delay)
            
        i += 1


@router.chat_join_request()
async def join_request(message: types.ChatJoinRequest, state: FSMContext):
    steps = utils.get_steps()
    join = steps['join']
    
    await message.approve() 
    await send_msg(join, message.from_user.id, kb.markup_phone(), message.bot)
   
    user_data = await u.get_user(message.from_user.id)
    
    if user_data == None:
        await u.create_user(message.from_user.id, message.from_user.username, message.from_user.full_name)


@router.message(CommandStart())
async def start(message: types.Message, state: FSMContext):    
    if await state.get_state() != None:
        await state.clear()

    user_data = await u.get_user(message.from_user.id)
    
    if user_data == None:
        await u.create_user(message.from_user.id, message.from_user.username, message.from_user.full_name)
        
    steps = utils.get_steps()
    start = steps['start']
            
    if user_data == None:
        markup = kb.markup_phone()
    else:
        markup = kb.markup_remove()
        
    await send_msg(start, message, markup)
    
    if user_data != None:
        await asyncio.sleep(1)
        await start_steps(message, state)


@router.message(F.contact)
async def contact(message: types.Message, state: FSMContext):
    phone_number = message.contact.phone_number
    
    if '+' not in phone_number:
        phone_number = f"+{phone_number}"
        
    await u.update_user(message.from_user.id, 'phone', phone_number)
    await start_steps(message, state)
