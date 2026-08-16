from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func
from sqlalchemy import CheckConstraint


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))
    #is_admin = db.Column(db.Boolean, default=False)
    log_readings = db.relationship('Log_reading', backref='user', lazy=True)
    #teacher_class = db.relationship('class_list', backref='teacher', lazy='joined')
    #Streak tracking fields
    current_streak = db.Column(db.Integer, default=0)
    last_streak = db.Column(db.Integer, default=0)
    last_activity_date = db.Column(db.Date, nullable=True) # Date of last completed activity
    streak_freezes = db.Column(db.Integer, CheckConstraint('streak_freezes <= 5'), default=0)      # Number of freezes owned
    freeze_used_today = db.Column(db.Boolean, default=False) # used to make sure multiple streak freezes aren't used at once
    date_freeze_used = db.Column(db.Date, nullable=True)

class ny_times_best_sellers(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime(timezone=True), default=func.now(), nullable=False)
    data = db.Column(db.JSON, nullable=False)

class background_info(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True, nullable=False)
    data = db.Column(db.JSON, nullable=False)

class Log_reading(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    genre = db.Column(db.String(150), nullable=False)
    author = db.Column(db.String(150), nullable=False)
    reading_time = db.Column(db.Integer, nullable=False)  # minutes read
    timestamp = db.Column(db.DateTime(timezone=True), default=func.now(), nullable=False)  # when logged
    
class Recommend(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    background_info = db.Column(db.JSON, nullable=False)
    common_author = db.Column(db.String(150), nullable=False)
    common_genre = db.Column(db.String(150), nullable=False)
    data = db.Column(db.JSON, nullable=False)
    
class goals(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_by = (db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False))
    created_at = db.Column(db.DateTime(timezone=True), default=func.now(), nullable=False)
    type_of_goal = db.Column(db.String(80), nullable=False)
    goal_text = db.Column(db.String(300), nullable=False)
    target = db.Column(db.String(160), nullable=False)
    due_date = db.Column(db.DateTime(timezone=True), nullable=False)
    done = db.Column(db.Boolean, default=False)

class weekly_goals(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    due_date = db.Column(db.DateTime(timezone=True), nullable=False)
    goal_text = db.Column(db.String(300), nullable=False)
    type_goal = db.Column(db.String(80), nullable=False)
    target = db.Column(db.String(160), nullable=False)

class currency_logs(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime(timezone=True), default=func.now(), nullable=False)
    where = db.Column(db.String(50), nullable=False)
    where_id = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Integer, CheckConstraint('amount <= 500'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)




"""
class class_list(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime(timezone=True), default=func.now(), nullable=False)
    class_name = db.Column(db.String(50), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    class_code = db.Column(db.String(8), unique=True, nullable=False)
"""

"""
class class_enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime(timezone=True), default=func.now(), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('class_list.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    classes = db.relationship('class_list', backref=db.backref('enrollments', cascade='all, delete-orphan'), lazy='joined')
    user_data = db.relationship('User', backref='involvement', lazy=True)
"""

    
