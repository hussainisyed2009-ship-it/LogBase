from flask import Flask, request, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    
    # Use environment variable for SECRET_KEY, fallback for local development
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    
    # Force HTTPS in production
    @app.before_request
    def enforce_https():
        if os.path.exists('/var/app/current'):  # Running on EB
            if not request.is_secure and request.headers.get('X-Forwarded-Proto') != 'https':
                url = request.url.replace('http://', 'https://', 1)
                return redirect(url, code=301)
    
    # Database configuration - use environment variable if available
    database_url = os.environ.get('DATABASE_URL')
    if database_url:

        # added in order to change db to postgres
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        # Production: use provided database URL (e.g., PostgreSQL RDS)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        # Development/EB default: use SQLite
        # Check if running on AWS EB (has /var/app/current)
        if os.path.exists('/var/app/current'):
            # On AWS EB: use /tmp which is always writable
            db_path = '/tmp/database.db'
        else:
            # Local development: use instance folder
            db_path = os.path.join(os.path.dirname(__file__), '..', 'instance', 'database.db')
        
        db_path = os.path.abspath(db_path)
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        # SQLite connection string with timeout for concurrent access
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}?timeout=30&check_same_thread=False'
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    from .views import views
    from .auth import auth
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        from .models import User
        return User.query.get(int(id))
    
    return app
