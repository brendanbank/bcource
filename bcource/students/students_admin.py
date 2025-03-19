
from bcource.admin.admin_views import AuthModelView
from bcource import db, table_admin
from bcource.models import Student, StudentType


class StudentAdmin(AuthModelView):
    permission = "admin-student-edit"
    form_columns = ["user", "studenttype", "practices"]
    column_list = ["user", "studenttype", "practices"]
    
table_admin.add_view(StudentAdmin(Student, db.session, category='Student'))
