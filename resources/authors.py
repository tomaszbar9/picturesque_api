from flask.views import MethodView
from flask_smorest import Blueprint, Page

from schemas import AuthorSchema

from models import AuthorModel


blp = Blueprint("authors", "authors", description="Operations on authors.")


@blp.route("/authors/")
class AuthorsList(MethodView):
    @blp.response(200, AuthorSchema(many=True))
    @blp.paginate()
    def get(self, pagination_parameters):
        authors = AuthorModel.query.all()
        pagination_parameters.item_count = len(authors)
        pager = Page(collection=authors, page_params=pagination_parameters)
        return pager.items


@blp.route("/authors/<int:id>")
class Authors(MethodView):
    @blp.response(200, AuthorSchema)
    def get(self, id):
        author = AuthorModel.query.get_or_404(id)
        return author
