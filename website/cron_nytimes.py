from . import create_app, db
from .models import ny_times_best_sellers
from .best_sellers import get_best_sellers
import json


app = create_app() # loads app by itself because it needs it to access db

with app.app_context():
    data = get_best_sellers()

    # filter out exactly what we need
    json_array = []
    for i, (title, author, book_image) in enumerate(data['results']['books'], start=1):
        entry = {
                "id": i,
                "title": title,
                "author": author,
                "cover": book_image
            }
            
        json_array.append(entry)
    print(json_array)

    # add to db, didnt have time before
    # then test
    # then shedule on the current pc
    # then create .platforms config so it runs on the server