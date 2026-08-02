from dotenv import load_dotenv
from sqlalchemy import text
from . import db, create_app


# loads the env file
load_dotenv('.env.production', override=True)

app = create_app()
with app.app_context():
    db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if 'postgres' in db_uri:
        db.session.execute(text("DROP SCHEMA public CASCADE;"))
        db.session.execute(text("CREATE SCHEMA public;"))
        db.session.commit()
    else:
        db.drop_all()

    db.create_all()
    print('Database tables created.')
