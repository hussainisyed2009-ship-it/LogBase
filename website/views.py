from flask import Blueprint, render_template, request, flash, json, jsonify, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import func
from datetime import datetime, timedelta, timezone
from .models import Log_reading, User, Recommend, goals, background_info
from . import db
import requests
from .llm import call_LLM, get_cover
from .goals import getGoals, get_goals_student
import secrets
import string
from .best_sellers import get_best_sellers

views = Blueprint('views', __name__)

@views.route('/survey', methods=['POST', 'GET'])
def survey():
    if request.method == 'POST':
        data = {
            "age": request.form.get('age_range'),
            "genres": request.form.getlist('genres'),
            "favorite_book": request.form.get('favorite_book'),
            "reason": request.form.getlist('motivation')
        }
        # commit to db
        new_info = background_info(user_id=current_user.id, data=data)
        db.session.add(new_info)
        db.session.commit()
        return redirect(url_for('views.home'))
    return render_template("survey.html", user=current_user)


# save data from api
@views.route("/api/book/save", methods=['POST'])
@login_required
def save_data():
# finish writing function
    # 1. Get the JSON payload sent from JavaScript
    data = request.get_json()
    
    # 2. Extract fields
    title = data.get('title')
    author = data.get('author')
    genre = data.get('genre')
    time = data.get('minutes')

   

    if not title or not author or not genre or not time:
        return jsonify({'error': 'all input boxes have to be filled'}), 400
    
    try:
        minutes = int(time)
        if minutes <= 0:
            raise ValueError()
    except Exception:
        return jsonify({"error": "Only numbers are allowed to be input for minutes"}), 400
    
    new_log = Log_reading(genre=genre or 'Unknown', author=author, reading_time=minutes, user_id=current_user.id, title=title)
    db.session.add(new_log)
    db.session.commit()
    flash('Reading Logged', category='success')
    return jsonify({"status": "success"}), 200
# getting book data from api
@views.route("/api/book/<isbn>")
def get_book(isbn):
    # Call Open Library from the server side

    response = requests.get(
        f"https://openlibrary.org/isbn/{isbn}.json",
        headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) husky-reading-log/1.0"}
    )
    print("Status:", response.status_code)
    print("Body:", response.text)
    if response.status_code != 200:
        return jsonify({"error": "Book not found"}), 404
    
    
    data = response.json()

    if "authors" in data and len(data["authors"]) > 0:
        # getting key
        author_key = data["authors"][0]["key"]
        # openlib api call
        author_response = requests.get(
        f"https://openlibrary.org{author_key}.json",
        headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) husky-reading-log/1.0"}
        )
        # parse json for author name
        author_data = author_response.json()
        author_name = author_data["name"]
        print(author_name)
    else:
        author_name = "unknown"
    # book title
    book_title = data["title"]
    print(book_title)
    # genre
    book_genre = data.get("subjects", ["unknown"])[0]
    print(book_genre)
    # cover
    isbn_13 = data["isbn_13"][0]
    book_cover = f"https://covers.openlibrary.org/b/isbn/{isbn_13}-M.jpg"
    # final returns lib
    book_data = {
        "title": book_title,
        "author": author_name,
        "genre": book_genre,
        "cover": book_cover
    }
    return jsonify(book_data)

# Helper functions for reading statistics
def get_most_read_author(user_id):
    """Get the author the user has read the most (by total minutes)"""
    result = db.session.query(
        Log_reading.author, 
        func.sum(Log_reading.reading_time).label('total_time')
    ).filter(Log_reading.user_id == user_id).group_by(Log_reading.author).order_by(
        func.sum(Log_reading.reading_time).desc()
    ).first()
    
    return result[0] if result else None

def get_most_read_genre(user_id):
    """Get the genre the user has read the most (by total minutes)"""
    result = db.session.query(
        Log_reading.genre, 
        func.sum(Log_reading.reading_time).label('total_time')
    ).filter(Log_reading.user_id == user_id).group_by(Log_reading.genre).order_by(
        func.sum(Log_reading.reading_time).desc()
    ).first()
    
    return result[0] if result else None
def get_reading_streak(user_id):
    """Get current reading streak (consecutive days with at least one log)"""
    from datetime import date
    
    # Get all unique dates the user has logged (ordered by date descending)
    logs = db.session.query(func.date(Log_reading.timestamp)).filter(
        Log_reading.user_id == user_id
    ).distinct().order_by(func.date(Log_reading.timestamp).desc()).all()
    
    if not logs:
        return 0
    
    streak = 1
    current_date = logs[0][0]
    
    # Check each log date against the previous one
    for log_date in logs[1:]:
        log_date = log_date[0]
        # If dates are consecutive (1 day apart), increment streak
        if (current_date - log_date).days == 1:
            streak += 1
            current_date = log_date
        else:
            # Streak broken
            break
    
    return streak

def get_all_reading_stats(user_id):
    """Get all reading statistics for a user"""
    stats = {
        'total_minutes': db.session.query(func.sum(Log_reading.reading_time)).filter(
            Log_reading.user_id == user_id
        ).scalar() or 0,
        'total_reads': db.session.query(func.count(Log_reading.id)).filter(
            Log_reading.user_id == user_id
        ).scalar() or 0,
        'most_read_author': get_most_read_author(user_id),
        'most_read_genre': get_most_read_genre(user_id),
    }
    return stats


@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    background = background_info.query.get(current_user.id)
    if background == None:
        return redirect(url_for('views.survey'))

    if request.method == 'POST':
        title = request.form.get('title')
        genre = request.form.get('genre')
        author = request.form.get('author')
        time = request.form.get('time')

        # basic validation
        if not author or len(author) <= 1 or len(title) <= 1:
            flash('Author/Title name is too short', category='error')
        else:
            try:
                minutes = int(time)
                if minutes <= 0:
                    raise ValueError()
            except Exception:
                flash('Please provide a valid number of minutes', category='error')
                return render_template("home.html", user=current_user)

            new_log = Log_reading(genre=genre or 'Unknown', author=author, reading_time=minutes, user_id=current_user.id, title=title)
            db.session.add(new_log)
            db.session.commit()
            flash('Reading Logged', category='success')
            return redirect(url_for('views.home'))

    # show user's logs (optional)
    logs = Log_reading.query.filter_by(user_id=current_user.id).all()
    return render_template("home.html", user=current_user, logs=logs)

@views.route('/achievement', methods=['GET'])
@login_required
def achievement():
    '''
    REMOVE ANY CLASS RELATED GOAL LOGIC, ALLOW USER'S TO CREATE GOALS FOR THEMSELVES

    Add 3 different types of goals:
     1. the basic minute based goals
     2. Goal where the user has to read book from their recommendations
     3. goal where the user has to read x number of different books in a certain period of time
    '''


    # time for right now
    now = datetime.now(timezone.utc)
    # looks for goals
    # loops over each enrolment
    # then for each enrollment, gets goal from enrollments, then looks at classes to find the class info, then looks at goals table
    all_goals =[goal for enrollment in current_user.involvement for goal in enrollment.classes.goals]
    data_list = []
    for goal in all_goals:
        # get total minutes only for that goal
        total_minutes = get_goals_student(current_user.id, goal.id)
        if goal.due_date >= now:
            # append to data list
            data_to_append = {
                'goal_desc': goal.goal_text,
                'target': goal.target_minutes,
                'complete_mins': total_minutes,
                'due': goal.due_date.strftime('%Y-%m-%d %H:%M'),
                'creation_date': goal.created_at.strftime('%Y-%m-%d %H:%M')
            }
            data_list.append(data_to_append)

    return render_template("achievement.html", user=current_user, goals=data_list)


@views.route('/leaderboards', methods=['GET'])
@login_required
def leaderboards():
    # Query total reading time per user (all-time, weekly, or monthly)
    timeframe = request.args.get('timeframe')

    # check
    if timeframe == 'This week':
        
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday()) # this gets the index of the day, ex. monday = 0
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0) # makes it so the first day of the week is only the day and not time
        leaderboard_data = (
                    db.session.query(User.first_name, func.sum(Log_reading.reading_time).label('total_minutes'))
                    .join(Log_reading, User.id == Log_reading.user_id)
                    .filter(Log_reading.timestamp >= start_of_week)
                    .group_by(User.id)
                    .order_by(func.sum(Log_reading.reading_time).desc())
                    .all()
        )
    elif timeframe == 'This month':
        # get the start of the month
        this_month = datetime.now()
        start_of_month = this_month.replace(hour=0, minute=0, second=0, microsecond=0, day=1)
        leaderboard_data = (
                    db.session.query(User.first_name, func.sum(Log_reading.reading_time).label('total_minutes'))
                    .join(Log_reading, User.id == Log_reading.user_id)
                    .filter(Log_reading.timestamp >= start_of_month)
                    .group_by(User.id)
                    .order_by(func.sum(Log_reading.reading_time).desc())
                    .all()
        )
    else:
        leaderboard_data = (
            db.session.query(User.first_name, func.sum(Log_reading.reading_time).label('total_minutes'))
            .join(Log_reading, User.id == Log_reading.user_id)
            .group_by(User.id)
            .order_by(func.sum(Log_reading.reading_time).desc())
            .all()
        )

    return render_template("leaderboards.html", user=current_user, leaderboard=leaderboard_data, timeframe=timeframe)

@views.route('/delete-log/<int:log_id>', methods=['POST'])
@login_required
def delete_log(log_id):
    log = Log_reading.query.get(log_id)
    if log and log.user_id == current_user.id:
        db.session.delete(log)
        db.session.commit()
        flash('Log deleted', category='success')
    return redirect(url_for('views.home'))



@views.route('profile', methods=['GET'])
@login_required
def profile():
    total_minutes = db.session.query(func.sum(Log_reading.reading_time)).filter(
        Log_reading.user_id == current_user.id
    ).scalar() or 0
    most_author = get_most_read_author(current_user.id)
    most_genre = get_most_read_genre(current_user.id)
    streak = get_reading_streak(current_user.id)
    return render_template("profile.html", user=current_user, total_minutes=total_minutes, most_genre = get_most_read_genre(current_user.id), most_author = get_most_read_author(current_user.id), reading_streak=streak)

@views.route('/recommendations', methods=['GET'])
@login_required
def recommend():

    '''
    GET NY BEST SELLERS LIST
    '''
    best_sellers = get_best_sellers()

    most_author = get_most_read_author(current_user.id)
    most_genre = get_most_read_genre(current_user.id)

    # If the user hasn't logged any readings yet, skip LLM calls and show empty state
    if not most_author or not most_genre:
        return render_template("recommendations.html", user=current_user, recommendations=None, loading=False)

    user_recommendation = Recommend.query.filter_by(user_id=current_user.id).first()

    # Check if cached data is fresh — if so, skip the LLM entirely
    needs_llm = (
        user_recommendation is None or
        user_recommendation.common_author != most_author or
        user_recommendation.common_genre != most_genre
    )

    if needs_llm:
        # Render loading page immediately — JS will call /api/fetch-recommendations
        return render_template("recommendations.html", user=current_user, recommendations=None, loading=True)

    # Cache is fresh, render instantly with no LLM call
    return render_template("recommendations.html", user=current_user, recommendations=user_recommendation.data, loading=False)


@views.route('/api/fetch-recommendations', methods=['GET'])
@login_required
def fetch_recommendations():
    most_author = get_most_read_author(current_user.id)
    most_genre = get_most_read_genre(current_user.id)

    # API guard: if the user has no logged books, don't call the LLM
    if not most_author or not most_genre:
        return jsonify([]), 200
    background = background_info.query.get(current_user.id)
    user_recommendation = Recommend.query.filter_by(user_id=current_user.id).first()

    response = call_LLM(most_author=most_author, most_genre=most_genre, background_info=background.data)

    if response is None:
        return jsonify({"error": "LLM unavailable, please try again later"}), 503

    try:
        response_json = json.loads(response)
        for book in response_json:
            cover_url = get_cover(book.get('title'))
            if cover_url is not None:
                book["image_url"] = cover_url
                print(book)
            else:
                book["image_url"] = None
    except json.JSONDecodeError as e:
        print("JSON decode error:", e)
        print("Raw LLM response:", response)
        return jsonify({"error": "Failed to parse AI response"}), 500

    # Save or update the DB cache
    if user_recommendation is None:
        new_row = Recommend(
            user_id=current_user.id,
            background_info = background.data,
            common_author=most_author or "None",
            common_genre=most_genre or "None",
            data=response_json
        )
        db.session.add(new_row)
    else:
        user_recommendation.common_author = most_author or "None"
        user_recommendation.common_genre = most_genre or "None"
        user_recommendation.background_info = background.data or "None"
        user_recommendation.data = response_json

    db.session.commit()
    return jsonify(response_json), 200

@views.route('/admin/goals/delete/<goalId>', methods=['DELETE'])
@login_required
def delete_goal(goalId):
    goal = goals.query.get(goalId)
    if goal:
        db.session.delete(goal)
        db.session.commit()
        flash('Goal Deleted', category='success')
    return jsonify([]), 200

@views.route('/admin', methods=['POST'])
@login_required
def add_goal():
    # Retrieve form data matching the 'name' attributes in the HTML form
    goal_text = request.form.get('goal_text')
    goal_minutes_str = request.form.get('target_minutes')
    goal_due_date_str = request.form.get('due_date')
    which_class_str = request.form.get('which_class') # dont need this anymore

    '''
    add in different types of goals
    '''

    if goal_text and goal_minutes_str and goal_due_date_str and which_class_str:
        try:
            # Convert target_minutes to integer
            target_minutes = int(goal_minutes_str)
            which_class = int(which_class_str)
            if target_minutes <= 0:
                raise ValueError()

            # Parse datetime-local string format ('YYYY-MM-DDTHH:MM') to datetime object
            due_date = datetime.strptime(goal_due_date_str, '%Y-%m-%dT%H:%M')
            
            new_goal = goals(goal_text=goal_text, target_minutes=target_minutes, due_date=due_date, which_class=which_class)
            db.session.add(new_goal)
            db.session.commit()
            flash('Goal Created!', category='success')
        except ValueError:
            flash('Target minutes must be a valid number greater than 0', category='error')
        except Exception as e:
            print("Error parsing due date:", e)
            flash('Invalid date or time format provided', category='error')
    else:
        flash('Error creating goal, please input all fields and try again', category='error')

    # Redirect back to the admin page to refresh the view and close the modal
    return redirect(url_for('views.admin_page'))

@views.route('/admin/goal/edit', methods=['POST'])
@login_required
def edit_goal():
    # Retrieve form data matching the 'name' attributes in the HTML form
    goal_id = request.form.get('goal_id')
    goal_text = request.form.get('goal_text')
    goal_minutes_str = request.form.get('target_minutes')
    goal_due_date_str = request.form.get('due_date')
    which_class_str = request.form.get('which_class') # dont need this anymore

    if goal_text and goal_minutes_str and goal_due_date_str and which_class_str:
        try:
            # Convert target_minutes to integer
            target_minutes = int(goal_minutes_str)
            which_class = int(which_class_str)
            if target_minutes <= 0:
                raise ValueError()

            # Parse datetime-local string format ('YYYY-MM-DDTHH:MM') to datetime object
            due_date = datetime.strptime(goal_due_date_str, '%Y-%m-%dT%H:%M')
            

            # Fetch the goal from the database by its ID
            goal = goals.query.get(goal_id)
            if goal:
                goal.goal_text = goal_text
                goal.target_minutes = target_minutes
                goal.due_date = due_date
                goal.which_class = which_class
                db.session.commit()
                
                flash('Goal Edited!', category='success')
            else:
                flash('Goal could not be edited, please try again', category='error')
        except ValueError:
            flash('Target minutes must be a valid number greater than 0', category='error')
        except Exception as e:
            print("Error parsing due date:", e)
            flash('Invalid date or time format provided', category='error')
    else:
        flash('Error editing goal, please input all fields and try again', category='error')

    # Redirect back to the admin page to refresh the view and close the modal
    return redirect(url_for('views.admin_page'))

