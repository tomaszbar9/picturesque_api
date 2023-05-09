from flask.views import MethodView
from flask_smorest import abort, Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import SQLAlchemyError

from db import db
from schemas import UserSchema

from models import PostModel, UserModel

blp = Blueprint("collections", "collections", description="Operations on collections.")


@blp.route("/collections/<int:post_id>")
class AddToCollection(MethodView):
    @blp.response(201, UserSchema(only=["collection"]))
    @jwt_required()
    def post(self, post_id):
        post = PostModel.query.get_or_404(post_id)
        user = UserModel.query.get_or_404(get_jwt_identity())

        if post in user.collection:
            abort(400, message="Post already in the collection.")

        if post in user.posts:
            abort(400, message="User cannot add own post to own collection.")

        user.collection.append(post)

        try:
            db.session.add(user)
            db.session.commit()
        except SQLAlchemyError:
            abort(500)

        return user

    @blp.response(201, UserSchema(only=["collection"]))
    @jwt_required()
    def delete(self, post_id):
        post = PostModel.query.get_or_404(post_id)
        user = UserModel.query.get_or_404(get_jwt_identity())

        if post not in user.collection:
            abort(400, message="Post not in the collection")

        user.collection.remove(post)

        try:
            db.session.add(user)
            db.session.commit()
        except SQLAlchemyError:
            abort(500)

        return user
