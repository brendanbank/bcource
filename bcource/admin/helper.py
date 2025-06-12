from wtforms import TextAreaField
from flask import current_app, abort, redirect, url_for, request
from flask_security import current_user
from bcource.models import Content
from bcource.models import Role, Permission
from bcource import db
from flask_admin.contrib.sqla import ModelView

def accessible_as_admin(role_name=current_app.config['BCOURSE_SUPER_USER_ROLE']):
    print (f'test role {role_name}')
    role = Role().query.filter(Role.name==role_name).first()
    print (f'test role query: {role_name}')
    if not role:
        
        role = Role(name=role_name)
        db.session.add(role)
        print (role)
        db.session.commit()
        
    return (
        current_user.is_active
        and current_user.is_authenticated
        and current_user.has_role(role)
    )
    
def accessible_by_permission(permission=current_app.config['BCOURSE_SUPER_USER_ROLE']):
    permissionObj = Permission().query.filter(Permission.name==permission).first()
    if not permissionObj:
        permissionObj = Permission(name=permission)
        db.session.add(permissionObj)
        db.session.commit()

    return (
        current_user.is_active
        and current_user.is_authenticated
        and current_user.has_permission(permission)
    )


def authorize_user():
    if current_app.config.get('SECURITY_AUTHORIZE_REQUEST'):
        has_permission = False
        for endpoint, roles in current_app.config.get('SECURITY_AUTHORIZE_REQUEST').items():
            url = url_for(endpoint)
            if url == request.path:
                for role in roles:
                    print (f'for role: {role}')
                    if accessible_as_admin(role):
                        has_permission = True
            #         else:
            #
            #             pass
            #             abort(403)
 
        print (f'has_permission: {has_permission}')

# Create customized model view class
class AuthModelView(ModelView):
    
    
    edit_template = 'admin/admin-edit.html'
    create_template = 'admin/admin-edit.html'
    list_template = 'admin/admin-list.html'
    
    

    def __init__(self, *args, **kwargs):   
        
        if not self.column_exclude_list:
            self.column_exclude_list = list()
            
        if not self.form_excluded_columns:
            self.form_excluded_columns = list()
        
        for f_name in ['password', 'update_datetime']:
            self.column_exclude_list.append(f_name)
            self.form_excluded_columns.append(f_name)
                        
        if not self.form_overrides:
            self.form_overrides = {}            

        self.form_overrides.update({ 'phone_number': PhoneField })
                
                    
        super(AuthModelView, self).__init__(*args, **kwargs) 

    def is_accessible(self):
        if hasattr(self, 'permission'):
            permission = self.permission
        else:
            permission = current_app.config['BCOURSE_SUPER_USER_ROLE']
        
        return accessible_by_permission(permission) or accessible_as_admin()
    
    
    def _handle_view(self, name, **kwargs):
        """
        Override builtin _handle_view in order to redirect users when a view is not
        accessible.
        """
        if not self.is_accessible():
            if current_user.is_authenticated:
                # permission denied
                abort(403)
            else:
                # login
                return redirect(url_for("security.login", next=request.url))

    def render(self, template, **kwargs):
        """
        using extra js in render method allow use
        url_for that itself requires an app context
        """
        if hasattr(self, "extra_js"):
            self.extra_js += [ 'https://cdn.jsdelivr.net/npm/intl-tel-input@25.3.0/build/js/intlTelInput.min.js',
                        '/static/local.js']
        else:
            self.extra_js = [ 'https://cdn.jsdelivr.net/npm/intl-tel-input@25.3.0/build/js/intlTelInput.min.js',
                        '/static/local.js']

        return super(AuthModelView, self).render(template, **kwargs)



from wtforms import TelField
from wtforms.widgets import TelInput

from wtforms import TextAreaField
from wtforms.widgets import TextArea

class CKTextAreaWidget(TextArea):
    def __call__(self, field, **kwargs):

        if kwargs.get('class'):
            kwargs['class'] += ' ckeditor'
        else:
            kwargs.setdefault('class', 'ckeditor')
            
        return super(CKTextAreaWidget, self).__call__(field, **kwargs)

class CKTextAreaField(TextAreaField):
    widget = CKTextAreaWidget()
    
class CkModelView(object):
    extra_js = ['//cdn.ckeditor.com/ckeditor5/44.3.0/ckeditor5.umd.js',
                '//cdn.ckeditor.com/ckeditor5-premium-features/44.3.0/ckeditor5-premium-features.umd.js',
                '//cdn.ckbox.io/ckbox/2.6.1/ckbox.js',
                '/static/ckeditor.js' ]
    
    def __init__(self, *args, **kwargs):

        if not hasattr(self, "ckfields"):
            self.ckfields = []
            
        if "ckfields" in kwargs:
            if hasattr(self, "ckfields"):
                self.ckfields += kwargs["ckfields"]
            del(kwargs["ckfields"])
            
        if self.form_overrides == None:
            self.form_overrides = {}
                
        for form_field in self.ckfields:
            self.form_overrides.update({ form_field: CKTextAreaField })
            
        super().__init__(*args, **kwargs) 

class PhoneWidget(TelInput):
    def __call__(self, field, **kwargs):
        if kwargs.get('class'):
            kwargs['class'] = 'phone_number ' + kwargs['class'] 
        else:
            kwargs.setdefault('class', 'phone_number')
            
        return super(PhoneWidget, self).__call__(field, **kwargs)

class PhoneField(TelField):
    widget = PhoneWidget()


class TagMixIn(object):
    def on_form_prefill(self, form, id):
        
        if self.tag_field:
            record = self.model.query.filter(id==id).first()
            pkkey= f'{record.__class__.__name__}_{id}'
            
            content = Content.get_tag(pkkey)
                        
            form[self.tag_field_name].data = content
            form[self.tag_field_name].label.text += f' (tag = {pkkey})'
        
        return super(TagMixIn, self).on_form_prefill(form, id)

    def __init__(self,*args, **kwargs):
        
        self.tag_field = None
        self.tag_field_name = None
        if "tag_field" in kwargs:
            self.tag_field = kwargs["tag_field"]
            self.tag_field_name = f'{self.tag_field}_2'
            self.tag_field_description = None
            
            self.column_exclude_list  = list((self.tag_field,))
            self.form_excluded_columns = list((self.tag_field,))
                                              
            del(kwargs["tag_field"])
            
            if not hasattr(self, "ckfields"):
                self.ckfields = []
                
            self.ckfields.append(self.tag_field_name)

        super(TagMixIn, self).__init__(*args, **kwargs) 
        
    def scaffold_form(self):
        form_class = super(TagMixIn, self).scaffold_form()
        setattr(form_class, self.tag_field_name, CKTextAreaField(self.tag_field))
        return form_class

    def after_model_change(self, form, model, is_created):
        
        if form[self.tag_field_name].data != None:
            pkkey= f'{model.__class__.__name__}_{model.id}'
            tag = Content.get_tag(pkkey, obj=True)
            
            tag.text = form[self.tag_field_name].data            
            
            setattr(model, self.tag_field, pkkey)
            
            self.session.commit()
                
        return super(TagMixIn, self).after_model_change(form, model, is_created)
