import peewee
import os
import logging
import atexit

logger = logging.getLogger(__name__)

# Local imports
from __init__ import app

if __name__ != '__main__':
    if os.path.exists('./{0}'.format(app.config['DB_NAME'])):
        DB_PATH = './{0}'.format(app.config['DB_NAME'])
    elif os.path.exists('./website/{0}'.format(app.config['DB_NAME'])):
        DB_PATH = './website/{0}'.format(app.config['DB_NAME'])
    else:
        logger.critical('database could not be located')
        # exit()
else:
    DB_PATH = './{0}'.format(app.config['DB_NAME'])

try:
    logger.debug('Database is at {}'.format(DB_PATH))
except NameError:
    db = None
else:
    db = peewee.SqliteDatabase(DB_PATH)


class BaseModel(peewee.Model):
    """ Base model with a handle to the database """
    class Meta:
        database = db


class Electricity(BaseModel):
    date = peewee.DateField()
    amount = peewee.FloatField()
    kwh = peewee.FloatField()

    def __str__(self):
        return "{} {} {}".format(self.date, self.amount, self.kwh)


class Event(BaseModel):
    date = peewee.DateField()
    name = peewee.CharField()
    deleted = peewee.BooleanField(default=False)


class Todo(BaseModel):
    event = peewee.ForeignKeyField(Event, related_name='todos', null=True)
    task = peewee.CharField()
    done = peewee.BooleanField(default=False)
    deleted = peewee.BooleanField(default=False)


class Bill(BaseModel):
    due = peewee.DateField()
    name = peewee.CharField()
    amount = peewee.FloatField()


# -----------Helper functions-----------
def before_request_handler(database=db):
    logger.debug('Opening connection to DB')
    database.connect()
    return


def after_request_handler(database=db):
    logger.debug('Closing connection to DB')
    try:
        database.close()
    except AttributeError:
        pass
    return
atexit.register(after_request_handler, db)


def create_tables():
    before_request_handler(db)
    db.create_tables([Electricity, Event, Todo, Bill], True)
    return


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s : %(name)s : %(levelname)s : %(message)s')
    before_request_handler()
    create_tables()
