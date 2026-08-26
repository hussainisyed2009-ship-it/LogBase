from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from .models import User
from werkzeug.security import generate_password_hash, check_password_hash
from . import db, mail
from flask_mailman import EmailMessage, EmailMultiAlternatives
from flask_login import login_user, login_required, logout_user, current_user
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from .verification import get_token


auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    data = request.form
    print(data)
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                if not user.email_verified:
                    key = current_app.config['SECRET_KEY']
                    token = get_token(email, key)
                    verify_url = url_for('auth.verify', token=token, _external=True)
                            
                    html_body = render_template('email_verify_account.html', verify_url=verify_url)
                    text_body = f"Click this link to verify your LogBase account: {verify_url}\n\nThis link will expire in 24 hours."
                    new_email = EmailMultiAlternatives(
                        subject="Verify LogBase Account",
                        body=text_body,
                        from_email=current_app.config['MAIL_USERNAME'],
                        to=[email]
                    )
                    new_email.attach_alternative(html_body, "text/html")
                    new_email.send()
                    flash('Account was not verified, please head over to email inbox to verify account.', category='error')
                    return redirect(url_for('auth.login'))
                flash('Logged In Succesfully', category='success')
                login_user(user, remember=True)
                return redirect(url_for('views.home'))
            else:
                flash('Incorrect password, please try again', category='error')
        else:
            flash('Email doesn not exist', category='error')

    return render_template("login.html", user=current_user)

@auth.route('/email_for_password', methods=['GET', 'POST'])
def email_for_pass():
    if request.method == 'POST':
        email = request.form.get('email')
        if len(email) >= 7:
            exist = User.query.filter_by(email=email.strip()).first()
            if not exist:
                flash('Please enter a valid email', category='error')
                return redirect(url_for('auth.email_for_pass'))
            key = current_app.config['SECRET_KEY']
            serializer = URLSafeTimedSerializer(key)
            token = serializer.dumps(email)
            reset_url = url_for('auth.change_pass', token=token, _external=True)

            html_body = render_template('email_reset_password.html', reset_url=reset_url)
            text_body = f"Click this link to reset your password: {reset_url}\n\nThis link will expire in 30 minutes."
            new_email = EmailMultiAlternatives(
                subject="LogBase Password Reset Link",
                body=text_body,
                from_email=current_app.config['MAIL_USERNAME'],
                to=[email]
            )
            new_email.attach_alternative(html_body, "text/html")
            new_email.send()
            flash('Please check you inbox for a password reset link', category='success')
            return redirect(url_for('auth.login'))
        else:
            flash('Please enter a valid email', category='error')
    return render_template("email_for_password.html", user=current_user)

@auth.route('/change/pass/<token>', methods=['GET', 'POST'])
def change_pass(token):
    try:
        # decode token
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        email = serializer.loads(token, max_age=1800)
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('User not found', category='error')
            return redirect(url_for('auth.sign_up'))
    except SignatureExpired:
        flash('Link is expired, please request link again.', category='error')
        return redirect(url_for('auth.email_for_pass'))
    except BadSignature:
        flash('Invalid URL, please request link again', category='error')
        return redirect(url_for('auth.email_for_pass'))

    if request.method == 'GET':
        return render_template("change_pass.html", user=current_user)
    if request.method == 'POST':
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        if password1 != password2:
            flash('Passwords must match.', category='error')
        elif len(password1) < 5:
            flash('Password is too short, must be atleast 5 charecters', category='error')
        else:
            password = generate_password_hash(password1, method='pbkdf2:sha256')

            user.password = password
            db.session.commit()
            flash('Password reset successfully', category='success')
            return redirect(url_for('auth.login'))
        

    return render_template("change_pass.html", user=current_user)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))




@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('FirstName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')


        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists', category='error')


        elif len(email) < 4:
            flash('Email is invalid, make sure to use a valid email address', category='error')
        elif len(first_name) < 2:
            flash('First name is invalid, first name should be longer than 2 charecters', category='error')
        elif password1 != password2:
            flash('Passwords do not match, please try again', category='error')
        elif len(password1) < 5:
            flash('Password is too short, it should be over 5 charecters long', category='error')
        else:
            new_user = User(email=email, first_name=first_name, password=generate_password_hash(password1, method='pbkdf2:sha256'), email_verified=False)
            db.session.add(new_user)
            db.session.commit()
            #login_user(new_user, remember=True)
            #return redirect(url_for('views.survey'))
            key = current_app.config['SECRET_KEY']
            token = get_token(email, key)
            verify_url = url_for('auth.verify', token=token, _external=True)

            html_body = render_template('email_verify_account.html', verify_url=verify_url)
            text_body = f"Click this link to verify your LogBase account: {verify_url}\n\nThis link will expire in 24 hours."
            new_email = EmailMultiAlternatives(
                subject="Verify LogBase Account",
                body=text_body,
                from_email=current_app.config['MAIL_USERNAME'],
                to=[email]
            )
            new_email.attach_alternative(html_body, "text/html")
            new_email.send()
            flash('Account created! Please head over to your email and verify your account', category='success')



    return render_template("sign_up.html", user=current_user)

@auth.route('/verify/<token>', methods=['GET', 'POST'])
def verify(token):
    try:
        # decode token
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        email = serializer.loads(token, max_age=86400)
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('User not found', category='error')
            return redirect(url_for('auth.sign_up'))
        if user.email_verified:
            flash('Email already verified', category='success')
            return redirect(url_for('auth.login'))
    except SignatureExpired:
        flash('Please login again and request a new URL because this link has expired.', category='error')
        return redirect(url_for('auth.login'))
    except BadSignature:
        flash('Invalid URL, please try a different URL or try again later.', category='error')
        return redirect(url_for('auth.sign_up'))

    user.email_verified = True
    db.session.commit()
    flash('Succesfully verified account, please login to continue.', category='success')
    return redirect(url_for('auth.login'))
        