from flask import current_app, make_response, render_template, redirect, flash, url_for, redirect, request, url_for
from flask_security import current_user, url_for_security
from bcource.home.home_views import home

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
    return (resp)
    # return redirect (url_for('home_bp.home'))

@current_app.errorhandler(404)
def not_found(error):
    
    msg = 'File not found!'
    flash(msg, 'error')
    resp = make_response(render_template('errors/errors.html', e=msg), 404)
    return resp

