from db import db


class AuthorModel(db.Model):
    __tablename__ = "authors"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    titles = db.relationship(
        "TitleModel", backref="author", lazy="dynamic")
    posts = db.relationship("PostModel", backref="author", lazy="dynamic")

    def __repr__(self):
        return f"<{self.name}>"
