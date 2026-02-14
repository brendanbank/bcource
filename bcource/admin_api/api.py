from flask import Blueprint, request
from flask_restx import Api, abort

admin_api_bp = Blueprint('admin_api', __name__, url_prefix='/admin-api')


@admin_api_bp.before_request
def protect_docs():
    """Require admin auth for Swagger UI and spec."""
    from bcource.admin_api.auth import _user_from_bearer_token, admin_required
    if request.path in ('/admin-api/docs', '/admin-api/swagger.json'):
        from flask_security import current_user
        user = _user_from_bearer_token()
        if user is None and current_user.is_authenticated:
            user = current_user
        if user is None:
            abort(401, 'Authentication required')
        if not user.is_active or not user.has_role('db-admin'):
            abort(403, 'Forbidden')

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
