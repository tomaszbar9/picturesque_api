from db import db


class TitleModel(db.Model):
    __tablename__ = "titles"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    author_id = db.Column(
        db.Integer, db.ForeignKey("authors.id"), unique=False, nullable=False
    )

    posts = db.relationship("PostModel", backref="title")

    def __repr__(self):
        return f"<{self.title}>"
