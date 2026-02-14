from flask_restx import Namespace, Resource
from bcource.admin_api.auth import admin_required
from bcource.admin_api.serializers import student_model
from bcource.admin_api.api import api
from bcource.models import Student, User, Practice
from sqlalchemy import or_

ns = Namespace('students', description='Student lookup')
api.add_namespace(ns)

parser = ns.parser()
parser.add_argument('q', type=str, help='Search by name or email', location='args')


@ns.route('/')
class StudentList(Resource):
    @ns.doc('search_students')
    @ns.expect(parser)
    @ns.marshal_list_with(student_model)
    @admin_required
    def get(self):
        """Search students by name or email."""
        args = parser.parse_args()
        practice = Practice.default_row()

        query = Student.query.join(User).filter(Student.practice_id == practice.id)

        q = args.get('q')
        if q:
            like = f'%{q}%'
            query = query.filter(or_(
                User.first_name.ilike(like),
                User.last_name.ilike(like),
                User.email.ilike(like),
            ))

        return query.order_by(User.last_name, User.first_name).limit(50).all()
