from . import db
from .models import goals, User, Log_reading, class_list, class_enrollment
from sqlalchemy import func



def getGoals(user):
    # what this does:
        # uses the relationships built into db
        # first it check the user's teacher_class element, which is a list of classes that they created
        # then it loops through the classes in those lists using the class_list's relationship to the goals table to get each goal and adds it to the list
    all_goal = [goal for single_class in user.teacher_class for goal in single_class.goals]
    return all_goal

def get_goals_student(studentId, goalId):
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

def get_goals_student_stats(studentId, goal):

    # query and filter by userId, and only get minutes from between
    # the time the goal was created and when it's due
    minutes_from_goal_creation = db.session.query(func.sum(Log_reading.reading_time)).filter(
        Log_reading.user_id == studentId,
        Log_reading.timestamp >= goal.created_at,
        Log_reading.timestamp <= goal.due_date
    ).scalar() or 0

    return minutes_from_goal_creation


