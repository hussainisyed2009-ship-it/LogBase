from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))
    is_admin = db.Column(db.Boolean, default=False)
    log_readings = db.relationship('Log_reading', backref='user', lazy=True)
    teacher_class = db.relationship('class_list', backref='teacher', lazy='joined')

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
    common_author = db.Column(db.String(150), nullable=False)
    common_genre = db.Column(db.String(150), nullable=False)
    data = db.Column(db.JSON, nullable=False)
    
class goals(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime(timezone=True), default=func.now(), nullable=False)
    which_class = db.Column(db.Integer, db.ForeignKey('class_list.id'), nullable=False)
    goal_text = db.Column(db.String(300), nullable=False)
    target_minutes = db.Column(db.Integer, nullable=False)
    due_date = db.Column(db.DateTime(timezone=True), nullable=False)
    class_data = db.relationship('class_list', backref=db.backref('goals', cascade='all, delete-orphan'), lazy=True)


class class_list(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime(timezone=True), default=func.now(), nullable=False)
    class_name = db.Column(db.String(50), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    class_code = db.Column(db.String(8), unique=True, nullable=False)


class class_enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime(timezone=True), default=func.now(), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('class_list.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    classes = db.relationship('class_list', backref=db.backref('enrollments', cascade='all, delete-orphan'), lazy='joined')
    user_data = db.relationship('User', backref='involvement', lazy=True)


    
