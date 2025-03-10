from flask import Blueprint, render_template, send_from_directory
from flask import current_app as app
from flask_security import current_user
import os
from flask_security import auth_required

# Blueprint Configuration
home_bp = Blueprint(
    'home_bp', __name__,
    # url_prefix="/home",
    template_folder='templates',
    static_folder='static'
)


@home_bp.route('/', methods=['GET'])
@auth_required()
def home():
    print (current_user)
    return render_template("home/index.html")

@home_bp.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')