import config
import peewee
from datetime import datetime
from .core import con, orm
from playhouse.postgres_ext import JSONField


class Mail(peewee.Model):
    """Class for Telegram Mail"""

    date_mail = peewee.DateTimeField()
    message_id = peewee.IntegerField()
    from_id = peewee.BigIntegerField()
    keyboard = JSONField(null=True)
    status = peewee.TextField(default='wait')
    
    class Meta:
        database = con   
        
    async def create_mail(self, date_mail, message_id, from_id, keyboard):
        """Create mail"""

        mail = await orm.create(Mail, date_mail=date_mail, message_id=message_id, from_id=from_id, keyboard=keyboard)
        pk = mail.id

        return pk
    
    
    async def get_mail(self, id):
        """Get mail data"""

        mails = await orm.execute(Mail.select().where(Mail.id == id).dicts())
        mails = list(mails)

        if mails != []:
            mail = mails[0]
        else:
            mail = None

        return mail
    
    
    async def update_mail(self, mail_id, key, value):
        """Update mail"""
        
        await orm.execute(Mail.update({key: value}).where(Mail.id == mail_id))
        
        
    async def delete_mail(self, mail_id):
        """Delete mail"""
                
        await orm.execute(Mail.delete().where(Mail.mail_id == mail_id))
        
        
    async def get_wait_mails(self):
        """Load all mails"""
        
        dt_now = datetime.now()
        
        mails = await orm.execute(Mail.select().where(
            Mail.status == 'wait',
            dt_now >= Mail.date_mail 
        ).dicts())
        mails = list(mails)
        
        return mails