import os
import datetime
from dotenv import load_dotenv

from flask_smorest import Blueprint, Page, abort
from flask.views import MethodView
from flask_jwt_extended import jwt_required, get_jwt_identity
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderUnavailable
from sqlalchemy.exc import SQLAlchemyError

import cloudinary
from cloudinary.exceptions import GeneralError
from cloudinary.uploader import upload, destroy

from db import db
from schemas import (
    PostSchema,
    PostUploadSchema,
    PostSearchSchema,
    PostResultSchema,
    PostUpdateSchema,
    PostUpdateUploadSchema,
)
from models import PostModel, AuthorModel, TitleModel

geolocator = Nominatim(user_agent="picturesque_api")

load_dotenv()

cloudinary.config(
    cloud_name=os.environ["CLOUDINARY_CLOUD_NAME"],
    api_key=os.environ["CLOUDINARY_API_KEY"],
    api_secret=os.environ["CLOUDINARY_API_SECRET"],
    secure=True,
)

blp = Blueprint("posts", "posts", description="Operations on posts.")


def create_unique_filename(filename):
    segments = filename.split("_")
    number_of_segments = len(segments)
    if number_of_segments > 2:
        segments[-1] = str(int(segments[-1]) + 1)
    else:
        segments.append("1")
    return f"{'_'.join(segments)}"


@blp.route("/posts/")
class PostsList(MethodView):
    @blp.arguments(PostSearchSchema, location="query")
    @blp.response(200, PostResultSchema(many=True))
    @blp.paginate()
    def get(self, search, pagination_parameters):
        collection = []
        if search:
            categories = []
            categories.append(
                [
                    {"found_in": "title", "post": post}
                    for post in PostModel.query.join(TitleModel)
                    .filter(TitleModel.title.ilike(f"%{search['q']}%"))
                    .all()
                ]
            )
            categories.append(
                [
                    {"found_in": "author", "post": post}
                    for post in PostModel.query.join(AuthorModel)
                    .filter(AuthorModel.name.ilike(f"%{search['q']}%"))
                    .all()
                ]
            )
            categories.append(
                [
                    {"found_in": "quote", "post": post}
                    for post in PostModel.query.filter(
                        PostModel.quote.ilike(f"%{search['q']}%")
                    ).all()
                ]
            )
            categories.append(
                [
                    {"found_in": "address", "post": post}
                    for post in PostModel.query.filter(
                        PostModel.address.ilike(f"%{search['q']}%")
                    ).all()
                ]
            )
            categories.sort(key=lambda x: len(x), reverse=True)
            for cat in categories:
                if len(cat) > 0:
                    collection.extend(cat)
        else:
            collection = [{"post": post} for post in PostModel.query.all()]
        pagination_parameters.item_count = len(collection)
        pager = Page(collection=collection, page_params=pagination_parameters)
        return pager.items

    @blp.arguments(PostSchema, location="form")
    @blp.arguments(PostUploadSchema, location="files")
    @blp.response(201, PostSchema)
    @jwt_required()
    def post(self, form_data, file_data):
        user_id = get_jwt_identity()
        author = form_data["author"]
        title = form_data["title"]
        quote = form_data["quote"]
        latitude = form_data.get("latitude", None)
        longitude = form_data.get("longitude", None)
        address = form_data.get("address", None)
        file = file_data["photo"]
        added = datetime.datetime.utcnow()

        if file.filename.rsplit(".", 1)[-1].lower() not in ("jpg", "png", "jpeg"):
            abort(422, message="Invalid format.")

        try:
            author_id = AuthorModel.query.filter_by(name=author).first().id
        except AttributeError:
            new_author = AuthorModel(name=author)
            db.session.add(new_author)
            db.session.flush()
            author_id = new_author.id

        title_in_db = TitleModel.query.filter_by(
            title=title, author_id=author_id
        ).first()
        if title_in_db:
            title_id = title_in_db.id
        else:
            new_title = TitleModel(title=title, author_id=author_id)
            db.session.add(new_title)
            db.session.flush()
            title_id = new_title.id

        if address:
            try:
                address_found = geolocator.geocode(address)
                if address_found:
                    latitude, longitude = (
                        address_found.latitude,
                        address_found.longitude,
                    )
            except GeocoderUnavailable:
                abort(404, message="Geocoder currently not available. Try later.")

        if latitude != None and longitude != None:
            try:
                address = geolocator.reverse(
                    f"{str(latitude)}, {str(longitude)}"
                ).address
            except GeocoderUnavailable:
                abort(404, message="Geocoder currently not available. Try later.")

        time_string = added.strftime("%y%m%d%H%M%S")
        filename = f"{user_id}_{time_string}"
        while filename in (post.filename for post in PostModel.query.all()):
            filename = create_unique_filename(filename)

        try:
            response = upload(
                file,
                public_id=filename,
                folder="picturesque",
                width=800,
                height=600,
                crop="limit",
            )
        except GeneralError as e:
            abort(400, message=str(e) or "Photo upload failed.")

        thumbnail_url = cloudinary.CloudinaryImage(response["public_id"]).image(
            gravity="auto", height=120, width=150, crop="thumb"
        )

        new_post = PostModel(
            user_id=user_id,
            author_id=author_id,
            title_id=title_id,
            quote=quote,
            latitude=latitude,
            longitude=longitude,
            address=address,
            filename=filename,
            thumbnail_url=thumbnail_url,
            photo_url=response["secure_url"],
            added=added,
        )

        db.session.add(new_post)
        try:
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            destroy(public_id=response["public_id"])
            abort(500)

        return new_post


@blp.route("/posts/<int:id>")
class Posts(MethodView):
    @blp.response(200, PostSchema)
    def get(self, id):
        post = PostModel.query.get(id)
        if not post:
            abort(400, message="Post does not exists.")
        return post

    @blp.arguments(PostUpdateSchema, location="form")
    @blp.arguments(PostUpdateUploadSchema, location="files")
    @blp.response(201, PostSchema)
    @jwt_required()
    def put(self, form_data, file_data, id):
        user_id = get_jwt_identity()
        post = PostModel.query.get(id)

        if not post:
            abort(400, message="Post does not exists.")
        if user_id != post.user_id:
            abort(401, message="Invalid token.")

        author = form_data.get("author", None)
        title = form_data.get("title", None)
        quote = form_data.get("quote", None)
        latitude = form_data.get("latitude", None)
        longitude = form_data.get("longitude", None)
        address = form_data.get("address", None)
        file = file_data.get("photo", None)

        if author:
            author_in_db = AuthorModel.query.filter_by(name=author).first()
            if author_in_db:
                author_id = author_in_db.id
            else:
                new_author = AuthorModel(name=author)
                db.session.add(new_author)
                db.session.flush()
                author_id = new_author.id
            post.author_id = author_id

        if title:
            if not author:
                author_id = post.author_id
            title_in_db = TitleModel.query.filter_by(title=title).first()
            if title_in_db:
                title_id = title_in_db.id
            else:
                new_title = TitleModel(title=title, author_id=author_id)
                db.session.add(new_title)
                db.session.flush()
                title_id = new_title.id
            post.title_id = title_id

        if quote:
            post.quote = quote

        if address:
            try:
                address_found = geolocator.geocode(address)
                if address_found:
                    latitude, longitude = (
                        address_found.latitude,
                        address_found.longitude,
                    )
            except GeocoderUnavailable:
                abort(404, message="Geocoder currently not available. Try later.")

        if latitude != None and longitude != None:
            try:
                address = geolocator.reverse(
                    f"{str(latitude)}, {str(longitude)}"
                ).address
                post.address = address
                post.latitude = latitude
                post.longitude = longitude
            except GeocoderUnavailable:
                abort(404, message="Geocoder currently not available. Try later.")

        if file:
            filename = post.filename

            try:
                response = upload(file, public_id=filename, folder="picturesque", width=800, height=600, crop="limit")
            except GeneralError as e:
                abort(400, message=str(e) or "Photo upload failed.")

            thumbnail_url = cloudinary.CloudinaryImage(response["public_id"]).image(gravity="auto", height=120, width=150, crop="thumb")

            post.thumbnail_url = (thumbnail_url,)
            post.photo_url = response["secure_url"]

        try:
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            abort(500)

        return post

    @jwt_required()
    def delete(self, id):
        user_id = get_jwt_identity()
        post = PostModel.query.get(id)

        if not post:
            abort(400, message="Post does not exists.")
        if user_id == post.user_id:
            try:
                db.session.delete(post)
                db.session.commit()

                public_id = "picturesque/" + post.filename
                destroy(public_id=public_id)
            except SQLAlchemyError:
                db.session.rollback()
                abort(500)
        else:
            abort(401, message="Invalid token.")

        title = TitleModel.query.get(post.title_id)
        author = AuthorModel.query.get(post.author_id)
        if len(title.posts) == 0:
            db.session.delete(title)

        if author.titles.count() == 0:
            db.session.delete(author)

        db.session.commit()

        return {"message": "Post successfully deleted."}, 200
