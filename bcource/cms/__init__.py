from flask import Blueprint

cms_bp = Blueprint(
    'cms_bp', __name__,
    url_prefix='/cms',
    template_folder='templates',
)

from . import cms_views  # noqa
