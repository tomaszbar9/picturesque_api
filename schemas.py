import re
from marshmallow import Schema, fields, validate, validates, ValidationError
from flask_smorest.fields import Upload


ALLOWED_EXTENSIONS = "image/jpeg", "image/png"


class PlainUserSchema(Schema):
    id = fields.Int(dump_only=True)
    username = fields.Str(required=True, validate=validate.Length(min=3, max=18))


class UserLoginSchema(PlainUserSchema):
    password = fields.Str(required=True, load_only=True)

    @validates("password")
    def validate_password(self, value):
        if len(value) < 8:
            raise ValidationError("Invalid password. Must be at least 8 characters.")
        elif not re.search(r"^[a-zA-Z0-9]*$", value):
            raise ValidationError(
                "Invalid password. Must consist of only letters and digits."
            )
        elif not re.search(r"[a-zA-Z]\d|\d[a-zA-Z]", value):
            raise ValidationError("Invalid password. Must contain letters and digits.")


class UserRegisterSchema(UserLoginSchema):
    confirm_password = fields.Str(required=True, load_only=True)


class PostSchema(Schema):
    id = fields.Int(dump_only=True)
    user_id = fields.Int(dump_only=True)
    author = fields.Str(required=True)
    title = fields.Str(required=True)
    quote = fields.Str(required=True)
    longitude = fields.Float(validate=validate.Range(min=-180, max=180))
    latitude = fields.Float(validate=validate.Range(min=-90, max=90))
    address = fields.Str(
        metadata={
            "description": "PicturesqueAPI first tries to locate the address, then the coordinates (if given)"
        }
    )
    filename = fields.Str(dump_only=True)
    thumbnail_url = fields.Str(dump_only=True)
    photo_url = fields.Str(dump_only=True)
    in_collection = fields.List(fields.Nested(PlainUserSchema()), dump_only=True)


class UserSchema(PlainUserSchema):
    collection = fields.List(
        fields.Nested(PostSchema(only=("id", "author", "title"))), dump_only=True
    )


class PostUploadSchema(Schema):
    photo = Upload(required=True, load_only=True)


class PostUpdateSchema(PostSchema):
    author = fields.Str(required=False)
    title = fields.Str(required=False)
    quote = fields.Str(required=False)


class PostUpdateUploadSchema(Schema):
    photo = Upload(required=False, load_only=True)


class PostSearchSchema(Schema):
    q = fields.Str()


class PostResultSchema(Schema):
    found_in = fields.Str()
    post = fields.Nested(PostSchema(exclude=["in_collection", "photo_url"]))


class PlainAuthorSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(dump_only=True)


class TitleSchema(Schema):
    id = fields.Int(dump_only=True)
    title = fields.Str(dump_only=True)
    author = fields.Nested(PlainAuthorSchema(), dump_only=True)
    posts = fields.List(fields.String(dump_only=True))


class AuthorSchema(PlainAuthorSchema):
    titles = fields.List(
        fields.Nested(TitleSchema(), exclude=["author"]), dump_only=True
    )
