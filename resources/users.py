from flask_smorest import Blueprint, Page, abort
from flask.views import MethodView
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
    get_jwt,
)
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError
from datetime import timedelta

from db import db, redis_jwt_blocklist
from schemas import UserSchema, UserRegisterSchema, UserLoginSchema, PostSchema
from models import UserModel, PostModel, CollectionModel


blp = Blueprint("users", "users", description="Operations on users.")


@blp.route("/register")
class UserRegister(MethodView):
    @blp.arguments(UserRegisterSchema)
    @blp.response(201, UserSchema)
    def post(self, user_data):
        if user_data["password"] != user_data["confirm_password"]:
            abort(400)
        try:
            user = UserModel(
                username=user_data["username"],
                password=generate_password_hash(
                    user_data["password"], method="pbkdf2:sha256", salt_length=8
                ),
            )

            db.session.add(user)
            db.session.commit()
        except IntegrityError:
            abort(409, message="A user with that name already exists.")

        return {"id": user.id, "username": user.username}

    @blp.arguments(UserRegisterSchema)
    def delete(self, user_data):
        user = UserModel.query.filter(
            UserModel.username == user_data["username"]
        ).first()
        if not user or user_data["password"] != user_data["confirm_password"]:
            abort(400)
        elif user and check_password_hash(user.password, user_data["password"]):
            db.session.delete(user)
            db.session.commit()
            return {"message": f"Successfully deleted user {user.username}."}, 200


@blp.route("/login")
class UserLogin(MethodView):
    @blp.arguments(UserLoginSchema)
    def post(self, user_data):
        user = UserModel.query.filter(
            UserModel.username == user_data["username"]
        ).first()

        if user and check_password_hash(user.password, user_data["password"]):
            access_token = create_access_token(identity=user.id, fresh=True, expires_delta=timedelta(minutes=5))
            refresh_token = create_refresh_token(identity=user.id)
            return {"access_token": access_token, "refresh_token": refresh_token}

        abort(401, message="Invalid credentials.")


@blp.route("/logout")
class UserLogout(MethodView):
    @jwt_required()
    def delete(self):
        jti = get_jwt()["jti"]
        redis_jwt_blocklist.set(jti, 1, ex=timedelta(hours=1))
        return {"message": "Successfully logged out."}, 200


@blp.route("/refresh")
class TokenRefresh(MethodView):
    @jwt_required(refresh=True)
    def post(self):
        current_user = get_jwt_identity()
        new_token = create_access_token(identity=current_user)
        return {"access_token": new_token}


@blp.route("/users/<int:id>/posts/")
class UsersPostsList(MethodView):
    @blp.response(200, PostSchema(many=True))
    @blp.paginate()
    def get(self, id, pagination_parameters):
        posts = PostModel.query.filter_by(user_id=id).all()
        pagination_parameters.item_count = len(posts)
        pager = Page(collection=posts, page_params=pagination_parameters)
        return pager.items


@blp.route("/users/<int:id>/collections/")
class UsersPostsList(MethodView):
    @blp.response(200, PostSchema(many=True))
    @blp.paginate()
    def get(self, id, pagination_parameters):
        posts = PostModel.query.filter(PostModel.in_collection.any(id=id)).all()
        pagination_parameters.item_count = len(posts)
        pager = Page(collection=posts, page_params=pagination_parameters)
        return pager.items


@blp.route("/users/recommendations/")
class UserRecommendations(MethodView):
    @blp.response(200, PostSchema(many=True))
    @blp.paginate()
    @jwt_required()
    def post(self, pagination_parameters):
        user_id = get_jwt_identity()
        user_choice = set(
            x.post_id for x in CollectionModel.query.filter_by(user_id=user_id).all()
        )

        users_who_chose_the_same = set()
        for post_id in user_choice:
            users_who_chose_the_post = set(
                x.user_id
                for x in CollectionModel.query.filter_by(post_id=post_id).all()
                if x.user_id != user_id
            )
            users_who_chose_the_same |= users_who_chose_the_post

        points_dict = {}
        for a_user in users_who_chose_the_same:
            a_user_likes = set(
                x.post_id for x in CollectionModel.query.filter_by(user_id=a_user).all()
            )

            a_users_points = len(user_choice & a_user_likes)

            user_posts = set(
                x.id for x in PostModel.query.filter_by(user_id=user_id).all()
            )
            a_user_distinct_likes = a_user_likes - user_choice - user_posts
            for post in a_user_distinct_likes:
                points_dict.setdefault(post, 0)
                points_dict[post] += a_users_points

        posts = (
            PostModel.query.filter(PostModel.id.in_(points_dict))
            .order_by(PostModel.id.desc())
            .all()
        )

        posts = sorted(posts, key=lambda x: points_dict[x.id], reverse=True)

        pagination_parameters.item_count = len(posts)
        pager = Page(collection=posts, page_params=pagination_parameters)
        return pager.items
