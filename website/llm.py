import os
from dotenv import load_dotenv
import requests
import re
import json


def call_LLM(most_author, most_genre, background_info): # change the backgroudn info passed in so it is a discription of the user
    # Load the environment variables from the production env file
    load_dotenv('.env.production', override=True)
    

    api_key = os.environ.get('OPENROUTER_API_KEY')  # api key
    if not api_key:
        raise RuntimeError('OPENROUTER_API_KEY not set in environment')

    # List of free models to try in order
    free_models = [
        "openrouter/free",
        "meta-llama/llama-3.3-70b-instruct:free",
        "google/gemma-2-9b-it:free",
        "mistralai/mistral-7b-instruct:free",
        "qwen/qwen-2.5-72b-instruct:free"
    ]

    prompt = (
        f"Here is the most read genre by a user: {most_genre}. "
        f"Here is the most read author: {most_author}. "
        f"Background info about this user: {background_info}. "
        f"Recommend 5 books for this user. "
        f"Return the recommendations ONLY as a raw JSON list of 5 objects. "
        f"Do not include any introductory text, markdown formatting, or code blocks (like ```json). "
        f"Each object in the JSON list must have exactly these keys: "
        f"1. 'title': The title of the book. "
        f"2. 'author': The name of the author. "
        f"3. 'date_written': The year the book was published/written."
    )

    for model_name in free_models:
        try:
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                data=json.dumps({
                    "model": model_name,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "reasoning": {"enabled": False}
                }),
                timeout=20
            )

            if response.status_code == 200:
                resp_json = response.json()
                content = resp_json['choices'][0]['message']['content']
                print(f"Successfully generated recommendations with {model_name}")
                return content
            elif response.status_code == 429:
                print(f"429 rate limit on {model_name}, trying next free model...")
                continue
            else:
                print(f"{response.status_code} error on {model_name}: {response.text}")
        except Exception as e:
            print(f"Exception calling {model_name}: {e}")
            continue

    return None

def get_cover(title):
    # call open lib search
    data = None
    try:
        response = requests.get(
            f"https://openlibrary.org/search.json?title={title}&limit=1",
            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) read-a-lot/1.0"},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
    except Exception as e:
        print("error getting data:", e)
        data = None

    if data and data.get("docs"):
        first_book = data["docs"][0]
        cover_id = first_book.get('cover_i')
        if cover_id is not None:
            return f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg"
        else:
            return None
    return None

