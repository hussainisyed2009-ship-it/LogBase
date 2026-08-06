from . import create_app, db
from .models import ny_times_best_sellers
from .best_sellers import get_best_sellers
import json
from dotenv import load_dotenv

# Load environment variables so Flask connects to PostgreSQL
load_dotenv('.env.production', override=True)


app = create_app() # loads app by itself because it needs it to access db

with app.app_context():
    data = get_best_sellers()

    # filter out exactly what we need
    json_array = []
    for i, book in enumerate(data['results']['books'], start=1):

        entry = {
                "id": i,
                "title": book.get('title'),
                "author": book.get('author'),
                "cover": book.get('book_image')
            }
            
        json_array.append(entry)
    # add to db, didnt have time before
    new_books = ny_times_best_sellers(data=json_array)
    db.session.add(new_books)
    db.session.commit()

    print("success")