from dotenv import load_dotenv
import os
from flask import json, jsonify
import requests


def get_best_sellers():
    # loads .env.production and parses it
    load_dotenv('.env.production', override=True)

    # this saves the exact key we want
    api_key = os.environ.get('NY_TIMEs_API_KEY')
    if not api_key: # just in case it doesnt work
        raise RuntimeError('key not available')

    #api call
    response = requests.get(
        url=f"https://api.nytimes.com/svc/books/v3/lists/current/hardcover-fiction.json?api-key={api_key}"
    )

    # check for errors
    if response.status_code == 200:
        response = response.json()
        print(response)
    else:
        print(response.status_code, 'error calling api')
        return

    return response # doesnt matter what we return here
