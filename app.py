import os
import warnings

from flask import Flask, jsonify
from flask_smorest import Api
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from dotenv import load_dotenv

from db import db, redis_jwt_blocklist
import models
from resources import (
    UsersBlueprint,
    PostsBlueprint,
    CollectionsBlueprint,
    AuthorsBlueprint,
    TitlesBlueprint,
)


def create_app(db_url=None):
    app = Flask(__name__)
    load_dotenv()

    app.config["PROPAGATE_EXCEPTIONS"] = True
    app.config["API_TITLE"] = "Picturesque REST API"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["OPENAPI_URL_PREFIX"] = "/"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
    app.config[
        "OPENAPI_SWAGGER_UI_URL"
    ] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url or os.getenv(
        "DATABASE_URL", "sqlite:///data.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
    app.config["THUMBNAIL_SIZE"] = 256, 256
    app.config["QUOTE_SAMPLE_LENGHT"] = 10
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")

    warnings.filterwarnings("ignore", message="Multiple schemas resolved to the name")

    db.init_app(app)
    migrate = Migrate(app, db)
    api = Api(app)
    jwt = JWTManager(app)

    @jwt.token_in_blocklist_loader
    def check_if_token_in_blocklist(jwt_header, jwt_payload):
        jti = jwt_payload["jti"]
        return bool(redis_jwt_blocklist.get(jti))

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return jsonify(
            {"description": "The token has been revoked.", "error": "token_revoked"},
            401,
        )

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return (
            jsonify({"message": "The token had expired.", "error": "token_expired"}),
            401,
        )

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return (
            jsonify(
                {"message": "Signature verification failed.", "error": "invalid_token"}
            ),
            401,
        )

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return (
            jsonify(
                {
                    "description": "Request does not contain an access token.",
                    "error": "authorization_required",
                }
            ),
            401,
        )

    api.register_blueprint(UsersBlueprint)
    api.register_blueprint(PostsBlueprint)
    api.register_blueprint(CollectionsBlueprint)
    api.register_blueprint(AuthorsBlueprint)
    api.register_blueprint(TitlesBlueprint)

    return app
