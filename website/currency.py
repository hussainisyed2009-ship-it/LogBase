from . import db
from .models import goals, User, Log_reading, Recommend, currency_logs
from sqlalchemy import func

def send_coins(where: str, where_id: int, amount: int, user_id: int):
    new_currency = currency_logs(where=where, where_id=where_id, amount=amount, user_id=user_id)
    db.session.add(new_currency)
    db.session.commit()