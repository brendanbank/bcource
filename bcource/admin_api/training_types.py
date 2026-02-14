from flask_restx import Namespace, Resource
from bcource.admin_api.auth import admin_required
from bcource.admin_api.serializers import training_type_model
from bcource.models import TrainingType, Practice

ns = Namespace('training-types', description='Training type lookup')

from bcource.admin_api.api import api
api.add_namespace(ns)


@ns.route('/')
class TrainingTypeList(Resource):
    @ns.doc('list_training_types')
    @ns.marshal_list_with(training_type_model)
    @admin_required
    def get(self):
        """List all training types for the current practice."""
        practice = Practice.default_row()
        return TrainingType.query.filter_by(practice_id=practice.id).order_by(TrainingType.name).all()
