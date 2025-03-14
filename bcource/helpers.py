from flask import current_app, make_response, render_template, redirect, flash

@current_app.errorhandler(403)
def not_authorized(error):
    msg = 'Permission denied!'
    # resp = make_response(render_template('errors/403.html'), 403)
    flash(msg, 'error')
    resp = make_response(render_template('errors/errors.html', e=msg), 403)
    return resp

@current_app.errorhandler(404)
def not_found(error):
    
    msg = 'File not found!'
    flash(msg, 'error')
    resp = make_response(render_template('errors/errors.html', e=msg), 404)
    return resp

