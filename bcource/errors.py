from flask import current_app, make_response, render_template, redirect, flash, url_for, redirect, request, url_for
from flask_security import current_user, url_for_security
from bcource.home.home_views import home

from werkzeug import exceptions
from flask_babel import lazy_gettext as _l
from flask_babel import _

class HTTPExceptionMustHaveTwoFactorEnabled(exceptions.HTTPException):
    code = 499
    description = _l('You must have two factor authentication enabled to use this feature!')


def handle_no_2fa(e):
    flash(e.description,'error')
    return render_template('handle_no_2fa.html')

class HTTPExceptionStudentNotActive(exceptions.HTTPException):
    code = 499
    description = _l('Student is not active!')


def student_not_actieve(e):
    # flash(e.description,'error')
    
    # return render_template('handle_student_not_active.html')
    resp = make_response(home(error_msg='no_active_status'), 200)
    return resp


@current_app.errorhandler(403)
def not_authorized(error):
    
    if current_user.is_anonymous:
        msg = 'Please sign in first!'
        # resp = make_response(render_template('errors/403.html'), 403)
        flash(msg, 'error')
        print (vars(request))
        return redirect (url_for_security('login', next=request.url))
        
        
    msg = 'Permission denied!'
    # resp = make_response(render_template('errors/403.html'), 403)
    flash(msg, 'error')
    resp = make_response(home(), 200)
    return redirect (url_for('home_bp.home'))

@current_app.errorhandler(404)
def not_found(error):
    
    msg = 'File not found!'
    flash(msg, 'error')
    resp = make_response(render_template('errors/errors.html', e=msg), 404)
    return resp
