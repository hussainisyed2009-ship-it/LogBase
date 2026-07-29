from dotenv import load_dotenv
from . import db, create_app


# loads the env file
load_dotenv('.env.production', override=True)

app = create_app()
with app.app_context():
    db.create_all()
    print('Database tables created.')
