from . import db
from .models import goals, User, Log_reading, class_list, class_enrollment
from sqlalchemy import func

def get_classes_for_teacher(teacherId):
    all_classes = class_list.query.filter(class_list.admin_id == teacherId).all()
    return all_classes

def get_all_students_for_class(classId):
    all_students = class_enrollment.query.filter(class_enrollment.class_id == classId).all()
    return all_students