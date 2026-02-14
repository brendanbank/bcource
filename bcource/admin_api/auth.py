from functools import wraps
from datetime import datetime, timezone, timedelta

import jwt
from flask import current_app, request
from flask_security import current_user, verify_and_update_password
from flask_restx import abort, Namespace, Resource

from bcource.models import User


def generate_admin_token(user):
    """Create a JWT for the given admin user."""
    exp_seconds = current_app.config['JWT_EXPIRATION_SECONDS']
    algorithm = current_app.config['JWT_ALGORITHM']
    payload = {
        'user_id': user.id,
        'email': user.email,
        'role': current_app.config['BCOURSE_SUPER_USER_ROLE'],
        'iat': datetime.now(timezone.utc),
        'exp': datetime.now(timezone.utc) + timedelta(seconds=exp_seconds),
    }
    return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm=algorithm)


def _user_from_bearer_token():
    """Decode a Bearer token and return the User, or None."""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None
    token = auth_header[7:]
    try:
        payload = jwt.decode(
            token,
            current_app.config['SECRET_KEY'],
            algorithms=[current_app.config['JWT_ALGORITHM']],
        )
    except jwt.ExpiredSignatureError:
        abort(401, 'Token has expired')
    except jwt.InvalidTokenError:
        abort(401, 'Invalid token')
    user = User.query.get(payload.get('user_id'))
    return user


def admin_required(f):
    """Decorator that requires db-admin role + 2FA, mirroring accessible_as_admin().

    Accepts both Bearer token and session-based authentication.
    JWT tokens skip the 2FA check (token itself proves identity via SECRET_KEY signature).
    Session-based auth still requires 2FA.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        via_jwt = False
        user = _user_from_bearer_token()
        if user is not None:
            via_jwt = True

        if user is None and current_user.is_authenticated:
            user = current_user

        if user is None:
            abort(401, 'Authentication required')

        if not user.is_active:
            abort(403, 'Account is not active')

        if not via_jwt and not user.tf_primary_method:
            abort(403, 'Two-factor authentication must be enabled')

        role_name = current_app.config['BCOURSE_SUPER_USER_ROLE']
        if not user.has_role(role_name):
            abort(403, 'db-admin role required')

        return f(*args, **kwargs)
    return decorated


# --- Token endpoint ----------------------------------------------------------

ns = Namespace('auth', description='Authentication token management')

from bcource.admin_api.api import api  # noqa: E402
api.add_namespace(ns)


@ns.route('/token')
class TokenResource(Resource):
    @ns.doc('create_token', security=None)
    def post(self):
        """Issue a JWT for an admin user.

        Accepts JSON: {"email": "...", "password": "..."}
        """
        data = request.get_json(silent=True) or {}
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            abort(400, 'email and password are required')

        user = User.query.filter_by(email=email).first()

        if user is None or not verify_and_update_password(password, user):
            abort(401, 'Invalid credentials')

        if not user.is_active:
            abort(403, 'Account is not active')

        if not user.tf_primary_method:
            abort(403, 'Two-factor authentication must be enabled')

        role_name = current_app.config['BCOURSE_SUPER_USER_ROLE']
        if not user.has_role(role_name):
            abort(403, 'db-admin role required')

        token = generate_admin_token(user)
        return {
            'token': token,
            'expires_in': current_app.config['JWT_EXPIRATION_SECONDS'],
        }
