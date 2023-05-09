from db import db
from datetime import datetime


class CollectionModel(db.Model):
    __tablename__ = "collections"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"))
    added = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
