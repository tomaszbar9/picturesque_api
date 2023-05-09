from datetime import datetime
from db import db


class PostModel(db.Model):
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("authors.id"), nullable=False)
    title_id = db.Column(db.Integer, db.ForeignKey("titles.id"), nullable=False)
    quote = db.Column(db.Text, nullable=False)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    address = db.Column(db.String)
    filename = db.Column(db.String(80), nullable=False)
    thumbnail_url = db.Column(db.String(256), nullable=False)
    photo_url = db.Column(db.String(256), nullable=False)
    added = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    in_collection = db.relationship(
        "UserModel", back_populates="collection", secondary="collections"
    )
