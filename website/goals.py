from . import db
from .models import goals, User, Log_reading, Recommend
from sqlalchemy import func



def getGoals(user):
    # adjusted to work
    all_goal = goals.query.filter(goals.created_by == user.id).all()
    return all_goal

def get_goals_student(studentId, goalId):
    # no need for adjustment

    # get goal first
    goal = goals.query.filter(goals.id == goalId).first()

    # query and filter by userId, and only get minutes from between
    # the time the goal was created and when it's due
    minutes_from_goal_creation = db.session.query(func.sum(Log_reading.reading_time)).filter(
        Log_reading.user_id == studentId,
        Log_reading.timestamp >= goal.created_at,
        Log_reading.timestamp <= goal.due_date
    ).scalar() or 0

    return minutes_from_goal_creation

def match_book_goal(userId, goalId, target):
    # get goal
    goal = goals.query.get(goalId)

    logs_from_goal_creation = Log_reading.query.filter(
        Log_reading.user_id == userId,
        Log_reading.timestamp >= goal.created_at,
        Log_reading.timestamp <= goal.due_date
    ).all() # logs from between created at and due date of goal

    for log in logs_from_goal_creation:
        if log.title.lower().strip() == target.lower().strip():
            return True

    return False


