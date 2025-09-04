import asyncio
import logging
import time
import aioschedule as schedule
from database import mail


logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(name)s - %(filename)s - %(message)s",
    filename='file.log'
)

m = mail.Mail()


async def checkMail():
    mails = await m.get_wait_mails()
    
    for mail in mails:
        mail_id = mail['id']
        message_id = mail['message_id']
        from_id = mail['from_id']
        keyboard = mail['keyboard']
                
        await m.update_mail(mail_id, 'status', 'run')
        
        keyboard = str(keyboard).replace(' ', '±').replace("'", '^').replace('"', '^')
        p = await asyncio.create_subprocess_shell(f'python -m fire mail start_mail --message_id={message_id} --from_id={from_id} --keyboard={keyboard}', shell=True, stdin=False, stdout=False, close_fds=False)
        
        
if __name__ == "__main__":
    schedule.every(10).seconds.do(checkMail)

    loop = asyncio.get_event_loop()
    while True:
        loop.run_until_complete(schedule.run_pending())
        time.sleep(1)