from flask import Blueprint
from flask_restx import Api

admin_api_bp = Blueprint('admin_api', __name__, url_prefix='/admin-api')

authorizations = {
    'Bearer': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization',
        'description': 'Enter: **Bearer &lt;token&gt;**. Get a token from POST /auth/token.',
    },
}

api = Api(
    admin_api_bp,
    version='1.0',
    title='Bcource Admin API',
    description='REST API for training and enrollment management',
    doc='/docs',
    authorizations=authorizations,
    security='Bearer',
)

# Namespaces are registered by importing endpoint modules below
from bcource.admin_api import locations      # noqa: E402, F401
from bcource.admin_api import training_types  # noqa: E402, F401
from bcource.admin_api import students        # noqa: E402, F401
from bcource.admin_api import trainings       # noqa: E402, F401
from bcource.admin_api import training_events # noqa: E402, F401
from bcource.admin_api import enrollments     # noqa: E402, F401
from bcource.admin_api import auth            # noqa: E402, F401
