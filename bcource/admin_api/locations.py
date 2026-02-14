from flask_restx import Namespace, Resource
from bcource.admin_api.auth import admin_required
from bcource.admin_api.serializers import location_model
from bcource.models import Location, Practice

ns = Namespace('locations', description='Location lookup')

from bcource.admin_api.api import api
api.add_namespace(ns)


@ns.route('/')
class LocationList(Resource):
    @ns.doc('list_locations')
    @ns.marshal_list_with(location_model)
    @admin_required
    def get(self):
        """List all locations for the current practice."""
        practice = Practice.default_row()
        return Location.query.filter_by(practice_id=practice.id).order_by(Location.name).all()
