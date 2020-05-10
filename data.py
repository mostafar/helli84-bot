
from tinydb import TinyDB, Query
import settings

_db = None
User = Query()

def db():
    global _db

    if _db is None:
        _db = TinyDB(settings.DATA_FILE_PATH)

    return _db


def get_message_dates(user_id):
    users = db().search(User.id == user_id)

    if len(users) == 0:
        return []

    if len(users) > 1:
        raise KeyError('More than one record found for the given user_id!')

    return users[0]['message_dates']


def set_message_dates(user_id, message_dates):
    db().upsert({
        'id': user_id,
        'message_dates': message_dates,
    }, User.id == user_id)
