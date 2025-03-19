from flask import Blueprint, render_template
from flask import current_app as app


# Blueprint Configuration
students_bp = Blueprint(
    'students_bp', __name__,
    url_prefix="/students",
    template_folder='templates',
    static_folder='static'
)


@students_bp.route('/', methods=['GET'])
def home():
    return render_template("home/index.html")