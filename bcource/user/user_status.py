from flask_babel import _
from flask_babel import lazy_gettext as _l
from bcource.policy import PolicyBase, HasData, DataIs
from flask_security import current_user
from bcource.models import Student, StudentStatus, StudentType, Practice, Role
from bcource.helpers import config_value as cv
from bcource import db

def post_validate_student_status(validator):
    if validator.status == False:
        if not current_user.student:
            
            studenttype = StudentType.default_row() #@UndefinedVariable
            studentstatus = StudentStatus.default_row() #@UndefinedVariable
            practice = Practice.default_row() #@UndefinedVariable
                 
            student=Student(user=current_user, 
                            studentstatus=studentstatus,
                            studenttype=studenttype,
                            practice=practice)
            
            db.session.add(student)
            db.session.commit()
            validator.validate()

def post_validate_student_has_role(validator):
    if validator.status == False:
        
        default_role = Role.default_row() #@UndefinedVariable
        
        if not default_role in current_user.roles:
            current_user.roles.append(default_role)
            db.session.commit()
        
        validator.validate()
            

class UserProfileChecks(PolicyBase):
    full_name = HasData(_l("Has Full Name"), variables=['first_name', 'last_name'],
                                bp_url='user_bp.update',
                                data_obj = current_user,
                                link_class="link-dark link-offset-2 link-underline-opacity-25 link-underline-opacity-100-hover")
    

    phone_number = HasData(_l("Has Phone Number"), variables=['phone_number'],
                                data_obj = current_user,
                                bp_url='user_bp.update',
                                link_class="link-dark link-offset-2 link-underline-opacity-25 link-underline-opacity-100-hover")
    
    emergency_contact = HasData(_l("Student has Emergency Contact"), variables=['usersettings.emergency_contact'],
                                data_obj = current_user,
                                bp_url='user_bp.settings',
                                msg_fail=_l("Student has no Emergency Contact!"),
    
                                link_class="link-dark link-offset-2 link-underline-opacity-25 link-underline-opacity-100-hover")
    
    student_status_data = HasData(_l('Student is registered'), 
                                  post_validate=post_validate_student_status, 
                                  bp_url='user_bp.index' , 
                                  data_obj = current_user,
                                    variables=['student'],
                                    link_class="link-dark link-offset-2 link-underline-opacity-25 link-underline-opacity-100-hover")
    
    student_role = DataIs(_l('Student as correct role'), 'student', bp_url='user_bp.index' , 
                                data_obj = current_user,
                                    post_validate=post_validate_student_has_role,
                                    variables=['roles.name'],
                                    link_class="link-dark link-offset-2 link-underline-opacity-25 link-underline-opacity-100-hover")

    student_status_active = DataIs('Student application is granted.',
                                   'active', 
                                   data_obj=current_user,
                                   bp_url='user_bp.index' ,
                                    variables=['student.studentstatus.name'],
                                    msg_fail=_l("Student application is in review!"),
                                    link_class="link-dark link-offset-2 link-underline-opacity-25 link-underline-opacity-100-hover")
    

