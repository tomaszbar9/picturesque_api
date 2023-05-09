import os
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
import redis

load_dotenv()

db = SQLAlchemy()

redis_jwt_blocklist = redis.from_url(
    os.getenv("REDIS_URL", os.environ["REDIS_BLOCKLIST_URL"])
)
