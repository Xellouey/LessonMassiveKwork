import asyncio
import config
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from handlers import client, admin, mail
from database import sql


bot = Bot(token=config.TOKEN, default=DefaultBotProperties(parse_mode='html'))


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        # filename='file.log'
    )

    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    dp.chat_join_request.filter(F.chat.id == config.CHAT_ID) # Принимаем заявки определённого канала
    dp.include_router(admin.router)
    dp.include_router(client.router)
    dp.include_router(mail.router)
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    sql.configure_database()
    asyncio.run(main())