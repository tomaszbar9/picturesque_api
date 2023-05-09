from db import db


class UserModel(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(18), unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    posts = db.relationship(
        "PostModel", backref="user", lazy="dynamic", cascade="all, delete-orphan"
    )
    collection = db.relationship(
        "PostModel", back_populates="in_collection", secondary="collections"
    )
