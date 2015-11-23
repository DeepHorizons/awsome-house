"""
Index for the website
"""

# Project imports
import flask
import logging
import flask_login

# Local imports
from __init__ import app
import models

logger = logging.getLogger(__name__)


@app.route('/electricity')
@flask_login.login_required
def electricity():
    return flask.render_template('electricity.html', title='Electricity')
