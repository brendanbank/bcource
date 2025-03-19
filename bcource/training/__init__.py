from flask import Blueprint, render_template, send_from_directory, g, flash
from flask import current_app as app
from flask_security import current_user
import os
from flask_security import auth_required
import flask_security.decorators as fsd

import bcource.training.training_admin

from bcource.training.training_views import training_bp
