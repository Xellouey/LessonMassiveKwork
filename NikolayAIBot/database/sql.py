from .user import User
from .mail import Mail
from .core import con
from playhouse.migrate import *


def configure_database():
    con.create_tables([User, Mail])


def drop_database():
    con.drop_tables([User])


def add_columns():
    migrator = PostgresqlMigrator(con)
    migrate(
    )