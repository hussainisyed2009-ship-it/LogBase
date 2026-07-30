import os
from dotenv import load_dotenv
import requests
import json
import re


def call_LLM(most_author, most_genre, background_info): # change the backgroudn info passed in so it is a discription of the user
    # Load the environment variables from the production env file
    load_dotenv('.env.production', override=True)
    

    api_key = os.environ.get('OPENROUTER_API_KEY')  # api key
    if not api_key:
        raise RuntimeError('OPENROUTER_API_KEY not set in environment')

    # api call

    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        data=json.dumps({
            "model": "google/gemma-4-26b-a4b-it:free",
            "messages": [
                {
                    "role": "user",
                    "content": f"Here is the most read genre by a user: {most_genre}. "
                               f"Here is the most read author: {most_author}. "
                               f"Background info about this user: {background_info}. "
                               f"Recommend 5 books for this user. "
                               f"Return the recommendations ONLY as a raw JSON list of 5 objects. "
                               f"Do not include any introductory text, markdown formatting, or code blocks (like ```json). "
                               f"Each object in the JSON list must have exactly these keys: "
                               f"1. 'title': The title of the book. "
                               f"2. 'author': The name of the author. "
                               f"3. 'date_written': The year the book was published/written. "
                               f"4. 'image_url': A cover image URL formatted as an Open Library cover link "
                               f"using the book's ISBN-13 (e.g., https://covers.openlibrary.org/b/isbn/{{isbn}}-M.jpg) "
                               f"or a placeholder image if the ISBN is unknown."
                }
            ],
            "reasoning": {"enabled": False}
        })
    )

    # Extract the assistant message
    if response.status_code == 200:
        response = response.json()
        response = response['choices'][0]['message']['content']
        print(response)
    else:
        print(response.status_code, "error calling api")
        return

    return response
