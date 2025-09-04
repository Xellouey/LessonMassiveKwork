import config
import peewee_async


con = peewee_async.PostgresqlDatabase(
    database=config.DB_NAME,
    user=config.DB_USER,
    host=config.DB_HOST,
    port=config.DB_PORT,
    password=config.DB_PASSWORD
)

orm = peewee_async.Manager(con)
