import requests
import random
from pathlib import Path
from db import db
from models import PostModel, UserModel
from app import create_app

photo_source = Path(__file__).parent / 'photos'

users = ["Alice", "Bob", "Charlie", "David", "Emily"]
PASSWORD = "q1111111"

url = "https://picturesque-r6r7.onrender.com"

for user in users:
    requests.post(url + "/register",
                  json={
                    "username": user,
                    "password": PASSWORD,
                    "confirm_password": PASSWORD,
                    })

authors = ['James Joyce', 'W.G. Sebald', 'Virginia Woolf', 'Edgar Allan Poe', "Henry James"]
titles = ['Ulysses', 'Austerlitz', 'To the Lighthouse', 'The Rings of Saturn', "Dubliners", "Loss of Breath", "Hop-Frog", "Washington Square", "The Turn of the Screw", "Mrs Dalloway"]
places = ['London', 'Dublin', 'Paris', 'Isle of Man, Douglas', 'Krakow']
quote = """Lorem ipsum dolor sit amet, consectetur adipisci elit, sed eiusmod tempor incidunt ut labore et dolore magna aliqua.
Ut enim ad minim veniam, quis nostrum exercitationem ullam corporis suscipit laboriosam, nisi ut aliquid ex 
ea commodi consequatur. Quis aute iure reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur."""


mixed = list(set(word for name in (authors + titles + places) for word in name.split()))

def get_access_token():
    name = random.choice(users)
    response = requests.post(
        url + "/login",
        json={
        "username": name,
        "password": PASSWORD
        }
    )
    return response.json()['access_token']

def create_quote():
    word = random.choice(mixed)
    splited_quote = quote.split()
    random_place = random.randrange(0, len(splited_quote))
    splited_quote.insert(random_place, word)
    return ' '.join(splited_quote)

popul_url = url + "/posts"

tokens = []
for u in users:
    tokens.append(get_access_token())
    
for photo in photo_source.iterdir():
    headers = {"Authorization": f"Bearer {random.choice(tokens)}"}
    files = {"photo": photo.open('rb')}
    data = {
                "title": random.choice(titles),
                "author": random.choice(authors),
                "quote": create_quote(),
                "address": random.choice(places),
            }
    response = requests.post(url=popul_url, data=data, files=files, headers=headers)
    
    
collection_url = url + "/collections"

app = create_app()
with app.app_context():
    ids = db.session.query(PostModel.id).all()
    users = UserModel.query.count()
for _ in range(users * 12):
    headers = {"Authorization": f"Bearer {random.choice(tokens)}"}
    response = requests.post(url=(collection_url + f"/{random.choice(ids)[0]}"), headers=headers)

