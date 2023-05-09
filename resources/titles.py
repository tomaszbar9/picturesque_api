from flask.views import MethodView
from flask_smorest import Blueprint, Page

from db import db
from schemas import TitleSchema

from models import TitleModel


blp = Blueprint("title", "titles", description="Operations on titles.")


@blp.route("/titles/")
class TitlesList(MethodView):
    @blp.response(200, TitleSchema(many=True))
    @blp.paginate()
    def get(self, pagination_parameters):
        titles = TitleModel.query.all()
        pagination_parameters.item_count = len(titles)
        pager = Page(collection=titles, page_params=pagination_parameters)
        return pager.items


@blp.route("/titles/<int:id>")
class Titles(MethodView):
    @blp.response(200, TitleSchema)
    def get(self, id):
        title = TitleModel.query.get_or_404(id)
        return title
