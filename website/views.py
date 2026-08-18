from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import func
from datetime import datetime, timedelta, timezone, date
from .models import Log_reading, User, Recommend, goals, background_info, ny_times_best_sellers, currency_logs
from . import db
import requests
from .llm import call_LLM, get_cover
from .goals import getGoals, get_goals_student, match_book_goal
import secrets
import string
from .best_sellers import get_best_sellers
import math
from .currency import send_coins
import json

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
    total_coins_user = db.session.query(func.sum(currency_logs.amount)).filter(currency_logs.user_id == current_user.id).scalar() or 0
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
        if minutes > 360:
            return jsonify({"error": "Please be honest with the minutes you input"}), 400
    except Exception:
        return jsonify({"error": "Only numbers are allowed to be input for minutes"}), 400
    
    # reward
    coins_to_add = 4
    if len(current_user.log_readings) > 0:
        for log in current_user.log_readings:
            if log.title.lower().strip() == title.lower().strip():
                coins_to_add = 2
                                    
        coins_to_add += math.floor(minutes/10)

    else:
        coins_to_add += math.floor(minutes/10)
    
    new_log = Log_reading(genre=genre or 'Unknown', author=author, reading_time=minutes, user_id=current_user.id, title=title)
    db.session.add(new_log)
    db.session.commit()


    if (coins_to_add + total_coins_user) < 500:
        recent_log = current_user.log_readings[-1]
        log_id = recent_log.id
        send_coins('log', log_id, coins_to_add, current_user.id)
        
        result = f'Reading Logged, {coins_to_add} coins added to wallet!'
    else:
        
        result = f'Reading Logged, however, no coins where added to wallet due to the wallet being full'


    if current_user.last_activity_date != date.today():
            streak = current_user.current_streak + 1
            current_user.current_streak = streak
            current_user.last_streak = 0
            current_user.last_activity_date = date.today()
            db.session.commit()
        

    flash(result, category='success')
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
        func.sum(Log_reading.reading_time).desc(), Log_reading.author.asc()
    ).first()
    
    return result[0] if result else None

def get_most_read_genre(user_id):
    """Get the genre the user has read the most (by total minutes)"""
    result = db.session.query(
        Log_reading.genre, 
        func.sum(Log_reading.reading_time).label('total_time')
    ).filter(Log_reading.user_id == user_id).group_by(Log_reading.genre).order_by(
        func.sum(Log_reading.reading_time).desc(), Log_reading.genre.asc()
    ).first()
    
    return result[0] if result else None

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
    total_coins_user = db.session.query(func.sum(currency_logs.amount)).filter(currency_logs.user_id == current_user.id).scalar() or 0
    if background == None:
        return redirect(url_for('views.survey'))

    if date.today() != current_user.date_freeze_used and current_user.freeze_used_today:
        current_user.freeze_used_today = False
        db.session.commit()


    """
    Check if streak should be broken
    """
    all_logs = current_user.log_readings
    if all_logs:
        most_recent_date = max(log.timestamp for log in all_logs).date()
        difference = (date.today() - most_recent_date).days

        if difference > 1 and not current_user.freeze_used_today:
            current_user.last_streak = current_user.current_streak
            current_user.current_streak = 0
            db.session.commit()
    else:
        current_user.last_streak = 0
        current_user.current_streak = 0
        db.session.commit()
            


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
                if minutes > 360:
                    flash('Please be honest with the amount of minutes you input', category='error')
                    return redirect(url_for('views.home'))

            except Exception:
                flash('Please provide a valid number of minutes', category='error')
                return redirect(url_for('views.home'))
            # reward
            coins_to_add = 4
            if len(current_user.log_readings) > 0:
                for log in current_user.log_readings:
                    if log.title.lower().strip() == title.lower().strip():
                        coins_to_add = 2
                coins_to_add += math.floor(minutes/10)
            else:
                coins_to_add += math.floor(minutes/10)
                
            new_log = Log_reading(genre=genre or 'Unknown', author=author, reading_time=minutes, user_id=current_user.id, title=title)
            db.session.add(new_log)
            db.session.commit()

            
            if (total_coins_user + coins_to_add) < 500:
                recent_log = current_user.log_readings[-1]
                log_id = recent_log.id
                send_coins('log', log_id, coins_to_add, current_user.id)
                
                result = f'Reading Logged, {coins_to_add} coins added to wallet!'
            else:
                
                result = f'Reading Logged, however, no coins where added to wallet due to the wallet being full'

            if current_user.last_activity_date != date.today():
                streak = current_user.current_streak + 1
                current_user.current_streak = streak
                current_user.last_streak = 0
                current_user.last_activity_date = date.today()
                db.session.commit()


            flash(result, category='success')
            return redirect(url_for('views.home'))
    streak = current_user.current_streak
    

    logs = Log_reading.query.filter_by(user_id=current_user.id).all()
    return render_template("home.html", user=current_user, logs=logs, streak=streak, coins=total_coins_user)

@views.route('/streak/restore', methods=['POST'])
@login_required
def restore_streak():
    if current_user.last_streak > 0:
        if current_user.streak_freezes > 0:
            current_user.current_streak = current_user.last_streak
            current_user.last_streak = 0
            current_user.streak_freezes -= 1
            current_user.freeze_used_today = True
            current_user.date_freeze_used = date.today()
            db.session.commit()
            flash("Streak restored successfully!", category='success')
        else:
            flash("You do not have any streak freezes available!", category='error')
    else:
        flash("Streak is still alive or no broken streak to restore!", category='error')
        
    return redirect(url_for('views.home'))


@views.route('/achievement', methods=['GET'])
@login_required
def achievement():
    all_user_goals = goals.query.filter(goals.created_by == current_user.id).all()
    # minute goal logic
    minutes_goals = [goal for goal in all_user_goals if goal.type_of_goal == 'minutes']
    minute_goal_list = []

    for mg in minutes_goals:
        is_done = False
        minutes = get_goals_student(current_user.id, mg.id) # get user minutes between time slot

        if minutes >= int(mg.target):
            is_done = True

        if is_done != mg.done:
            mg.done = is_done
            db.session.commit()


        append = {
            'id': mg.id,
            'created_at': mg.created_at,
            'desc': mg.goal_text,
            'target': mg.target,
            'due_date': mg.due_date,
            'done': is_done
        }
        minute_goal_list.append(append)

    # goals where user has to read a book from recommendations
    rec_goals = [rec_goal for rec_goal in all_user_goals if rec_goal.type_of_goal == 'recommended']
    rec_goal_list = [] # data on wether they completed the goal or not
    rec_book_list = [] # book titles from recommendations

    for rec in rec_goals:
        rec_is_done = match_book_goal(current_user.id, rec.id, rec.target)

        if rec.done != rec_is_done:
            rec.done = rec_is_done
            db.session.commit()

        rec_append = {
            'id': rec.id,
            'created_at': rec.created_at,
            'desc': rec.goal_text,
            'target': rec.target,
            'due_date': rec.due_date,
            'done': rec_is_done
        }
        rec_goal_list.append(rec_append)
    # fetch recommendations
    rec = Recommend.query.filter(Recommend.user_id == current_user.id).first() # could be None
    if rec is not None:
        data = rec.data
        for book in data:
            rec_book_list.append(book.get('title'))

    # specific book goals
    specific_book_goals = [spec_goal for spec_goal in all_user_goals if spec_goal.type_of_goal == 'specific']
    spec_stats = []

    for spec in specific_book_goals:
        spec_is_done = match_book_goal(current_user.id, spec.id, spec.target)

        if spec.done != spec_is_done:
            spec.done = spec_is_done
            db.session.commit()

        spec_append = {
            'id': spec.id,
            'created_at': spec.created_at,
            'desc': spec.goal_text,
            'target': spec.target,
            'due_date': spec.due_date,
            'done': spec_is_done
        }
        spec_stats.append(spec_append)

        
    

    return render_template("achievement.html", user=current_user, minute_goal_stats=minute_goal_list, unique_goal_stats=spec_stats, recommendation_goal_stats=rec_goal_list, rec_books=rec_book_list)


@views.route('/leaderboards', methods=['GET'])
@login_required
def leaderboards():
    # Query total reading time per user (all-time, weekly, or monthly)
    timeframe = request.args.get('timeframe', 'all')

    # Query leaderboard data based on timeframe
    if timeframe == 'weekly' or timeframe == 'This week':
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
        query = (
            db.session.query(User.id, User.first_name, func.sum(Log_reading.reading_time).label('total_minutes'))
            .join(Log_reading, User.id == Log_reading.user_id)
            .filter(Log_reading.timestamp >= start_of_week)
            .group_by(User.id)
            .order_by(func.sum(Log_reading.reading_time).desc(), User.first_name.asc())
        )
    elif timeframe == 'monthly' or timeframe == 'This month':
        this_month = datetime.now()
        start_of_month = this_month.replace(hour=0, minute=0, second=0, microsecond=0, day=1)
        query = (
            db.session.query(User.id, User.first_name, func.sum(Log_reading.reading_time).label('total_minutes'))
            .join(Log_reading, User.id == Log_reading.user_id)
            .filter(Log_reading.timestamp >= start_of_month)
            .group_by(User.id)
            .order_by(func.sum(Log_reading.reading_time).desc(), User.first_name.asc())
        )
    else:
        query = (
            db.session.query(User.id, User.first_name, func.sum(Log_reading.reading_time).label('total_minutes'))
            .join(Log_reading, User.id == Log_reading.user_id)
            .group_by(User.id)
            .order_by(func.sum(Log_reading.reading_time).desc(), User.first_name.asc())
        )

    full_leaderboard_data = query.all()

    # Determine current user's rank and total minutes in this timeframe
    user_rank = "Unranked"
    user_minutes = 0

    for rank, row in enumerate(full_leaderboard_data, start=1):
        if row.id == current_user.id:
            user_rank = f"#{rank}"
            user_minutes = row.total_minutes
            break

    # Limit leaderboard list to top 10
    top_10_leaderboard = [(row.first_name, row.total_minutes) for row in full_leaderboard_data[:10]]

    return render_template(
        "leaderboards.html",
        user=current_user,
        leaderboard=top_10_leaderboard,
        timeframe=timeframe,
        user_rank=user_rank,
        user_minutes=user_minutes
    )

@views.route('/delete-log/<int:log_id>', methods=['POST'])
@login_required
def delete_log(log_id):
    log = Log_reading.query.get(log_id)
    if log and log.user_id == current_user.id:
        db.session.delete(log)
        db.session.commit()

        currency = currency_logs.query.filter(currency_logs.where == 'log' and currency_logs.where_id == log.id).first()
        if currency:
            db.session.delete(currency)
            db.session.commit()
        else:
            currency = currency_logs.query.filter(currency_logs.where == 'log' and currency_logs.where_id == 0).first()
            if currency:
                db.session.delete(currency)
                db.session.commit()

        flash('Log deleted', category='success')
    return redirect(url_for('views.home'))



@views.route('profile', methods=['GET'])
@login_required
def profile():
    total_minutes = db.session.query(func.sum(Log_reading.reading_time)).filter(
        Log_reading.user_id == current_user.id
    ).scalar() or 0
    streak = current_user.current_streak
    return render_template("profile.html", user=current_user, total_minutes=total_minutes, most_genre = get_most_read_genre(current_user.id), most_author = get_most_read_author(current_user.id), reading_streak=streak)

@views.route('/recommendations', methods=['GET'])
@login_required
def recommend():

    '''
    GET NY BEST SELLERS LIST
    '''
    best_sellers = ny_times_best_sellers.query.order_by(ny_times_best_sellers.created_at.desc()).first()

    most_author = get_most_read_author(current_user.id)
    most_genre = get_most_read_genre(current_user.id)

    # If the user hasn't logged any readings yet, skip LLM calls and show empty state
    if not most_author or not most_genre:
        return render_template("recommendations.html", user=current_user, recommendations=None, best_sellers=best_sellers, loading=False)

    user_recommendation = Recommend.query.filter_by(user_id=current_user.id).first()

    # Normalize for comparison
    def _norm(s):
        return (s or '').strip().lower()

    # Check if cached data is fresh — if so, skip the LLM entirely
    needs_llm = (
        user_recommendation is None or
        _norm(user_recommendation.common_author) != _norm(most_author) or
        _norm(user_recommendation.common_genre) != _norm(most_genre)
    )

    if needs_llm:
        # Render loading page immediately — JS will call /api/fetch-recommendations
        return render_template("recommendations.html", user=current_user, recommendations=None, best_sellers=best_sellers, loading=True)

    # Cache is fresh, render instantly with no LLM call
    return render_template("recommendations.html", user=current_user, recommendations=user_recommendation.data, best_sellers=best_sellers, loading=False)


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
    author_val = most_author or ""
    genre_val = most_genre or ""
    bg_val = background.data if background else None

    if user_recommendation is None:
        new_row = Recommend(
            user_id=current_user.id,
            background_info=bg_val,
            common_author=author_val,
            common_genre=genre_val,
            data=response_json
        )
        db.session.add(new_row)
    else:
        user_recommendation.common_author = author_val
        user_recommendation.common_genre = genre_val
        user_recommendation.background_info = bg_val
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
    goal_target = request.form.get('target') # need to change name in html, can also be a string depending on type
    goal_type = request.form.get('tyep') # needs to be added to html
    goal_due_date_str = request.form.get('due_date')

    '''
    add in different types of goals
    '''

    if goal_text and goal_target and goal_due_date_str and goal_type:
        try:
            # Parse datetime-local string format ('YYYY-MM-DDTHH:MM') to datetime object
            due_date = datetime.strptime(goal_due_date_str, '%Y-%m-%dT%H:%M')
            if goal_type == 'minutes':
                # Convert target_minutes to integer
                if len(goal_text) <= 4:
                    flash('Goal description needs to be longer', category='error')

                target = int(goal_target)
                if target <= 0:
                    raise ValueError()
                
                new_goal = goals(created_by=current_user.id, type_of_goal=goal_type, goal_text=goal_text, target=target, due_date=due_date)
                db.session.add(new_goal)
                db.session.commit()
                flash('Goal Created!', category='success')
            elif goal_type == 'recommended':
                if len(goal_text) <= 4:
                    flash('Goal description needs to be longer', category='error')

                new_goal = goals(created_by=current_user.id, type_of_goal=goal_type, goal_text=goal_text, target=goal_target, due_date=due_date)
                db.session.add(new_goal)
                db.session.commit()
                flash('Goal Created!', category='success')
            elif goal_type == 'specific':
                if len(goal_text) <= 4:
                    flash('Goal description needs to be longer', category='error')

                new_goal = goals(created_by=current_user.id, type_of_goal=goal_type, goal_text=goal_text, target=goal_target, due_date=due_date)
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
    return redirect(url_for('views.achievement'))

@views.route('/admin/goal/edit', methods=['POST'])
@login_required
def edit_goal():
     # Retrieve form data matching the 'name' attributes in the HTML form
    goal_text = request.form.get('goal_text')
    goal_target = request.form.get('target') # need to change name in html, can also be a string depending on type
    goal_type = request.form.get('tyep') # needs to be added to html
    goal_due_date_str = request.form.get('due_date')
    goal_id = request.form.get('goal-id')

    '''
    add in different types of goals
    '''

    if goal_text and goal_target and goal_due_date_str and goal_type:
        goal = goals.query.get(goal_id)
        try:
            # Parse datetime-local string format ('YYYY-MM-DDTHH:MM') to datetime object
            due_date = datetime.strptime(goal_due_date_str, '%Y-%m-%dT%H:%M')
            if goal_type == 'minutes':
                # Convert target_minutes to integer
                if len(goal_text) <= 4:
                    flash('Goal description needs to be longer', category='error')
                    return redirect(url_for('views.achievement'))

                target = int(goal_target)
                if target <= 0:
                    raise ValueError()
                
                goal.goal_text = goal_text
                goal.target = target
                goal.type_of_goal = goal_type
                goal.due_date = due_date
                db.session.commit()
                flash('Goal Created!', category='success')
                return redirect(url_for('views.achievement'))
            elif goal_type == 'recommended':
                if len(goal_text) <= 4:
                    flash('Goal description needs to be longer', category='error')
                    return redirect(url_for('views.achievement'))

                goal.goal_text = goal_text
                goal.target = goal_target
                goal.type_of_goal = goal_type
                goal.due_date = due_date
                db.session.commit()
                flash('Goal Created!', category='success')
            elif goal_type == 'specific':
                if len(goal_text) <= 4:
                    flash('Goal description needs to be longer', category='error')
                    return redirect(url_for('views.achievement'))

                goal.goal_text = goal_text
                goal.target = goal_target
                goal.type_of_goal = goal_type
                goal.due_date = due_date
                db.session.commit()
                flash('Goal Created!', category='success')
            
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
    return redirect(url_for('views.achievement'))

