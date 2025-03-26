
from bcource.admin.admin_views import AuthModelView
from bcource import db, table_admin
from bcource.models import Student, StudentType, StudentStatus


class StudentAdmin(AuthModelView):
    permission = "admin-student-edit"
    form_columns = ["user", "studenttype", "studentstatus", "practice"]
    column_list = ["user", "studenttype", "studentstatus", "practice"]
    
table_admin.add_view(StudentAdmin(Student, db.session, category='Student'))

class StudentTypeAdmin(AuthModelView):
    permission = "admin-studenttype-edit"

class StudentStatusAdmin(AuthModelView):
    permission = "admin-studenttype-edit"

table_admin.add_view(StudentTypeAdmin(StudentType, db.session, category='Student'))
table_admin.add_view(StudentTypeAdmin(StudentStatus, db.session, category='Student'))
