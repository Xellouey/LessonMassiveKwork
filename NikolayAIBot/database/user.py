import config
import peewee
from datetime import datetime
from .core import con, orm


class User(peewee.Model):
    """Class for Telegram user"""

    user_id = peewee.BigIntegerField(unique=True)
    date_registered = peewee.DateTimeField(default=datetime.now)
    username = peewee.TextField(null=True)
    full_name = peewee.TextField()
    phone = peewee.TextField(null=True)
    
    class Meta:
        database = con   
        
    async def create_user(self, user_id, username, full_name):
        """Create user"""

        user = await orm.create(User, user_id=user_id, username=username, full_name=full_name)
        pk = user.id

        return pk
    
    
    async def get_user(self, id):
        """Get user data"""

        users = await orm.execute(User.select().where(User.user_id == id).dicts())
        users = list(users)

        if users != []:
            user = users[0]
        else:
            user = None

        return user
    
    
    async def update_user(self, user_id, key, value):
        """Update user"""
        
        await orm.execute(User.update({key: value}).where(User.user_id == user_id))
        
        
    async def delete_user(self, user_id):
        """Delete user"""
                
        await orm.execute(User.delete().where(User.user_id == user_id))
        
        
    async def get_all_users(self):
        """Load all users"""
        
        users = await orm.execute(User.select().dicts())
        users = list(users)
        
        return users