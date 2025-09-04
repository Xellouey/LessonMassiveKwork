import asyncio
import aiogram
import config
import logging
import config
import json
from database import user
import keyboards as kb


u = user.User()
bot = aiogram.Bot(config.TOKEN)


logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    filename='file.log'
)


async def mailing(message_id, from_id, keyboard):
    print(f'Start mailing {message_id}, from {from_id}')
    logging.info(f'Start mailing {message_id}, from {from_id}')

    users = await u.get_all_users()

    if keyboard != None:
        keyboard = keyboard.replace('±', ' ')
        keyboard = keyboard.replace("^", "'")
        keyboard = keyboard.replace('^', '"')
        keyboard = keyboard.replace("'", '"')
        
        keyboard = json.loads(keyboard)
        markup = kb.markup_custom(keyboard)
    else:
        markup = None
        
    i = 0
    for user in users:
        user_id = user['user_id']
    
        try:
            await bot.copy_message(user_id, from_id, message_id, reply_markup=markup)
            i += 1
        except Exception as e:
            print(e)
            
    print(f'Success mailing {message_id}, from {from_id}')
    logging.info(f'Success mailing ({i}/{len(users)}) {message_id}, from {from_id}')
    
    for admin in config.ADMINS:
        try:
            await bot.send_message(admin, f'📬 Рассылка ({i}/{len(users)})')
        except:
            pass


def start_mail(message_id, from_id, keyboard):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(mailing(message_id, from_id, keyboard))

