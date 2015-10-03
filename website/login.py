"""
login module
"""

# Project imports
import flask
import logging
import flask_login
import peewee
import hashlib
import os
import base64

logger = logging.getLogger(__name__)

# Local imports
from __init__ import app
import models
import forms

login_manager = flask_login.LoginManager()
login_manager.init_app(app)


class User(flask_login.UserMixin):
    """ This is the user class that is used for Flask-Login
    It should have all the properties of the User class in
    models.py
    """
    def __init__(self, login_name):
        try:
            user = models.User.get(models.User.login_name == login_name)
        except peewee.DoesNotExist:
            logger.warning("User with login_name '{0}' not found".format(login_name))
            raise LookupError('User not found')
        else:
            self.id = login_name
            self.name = user.name
            self.login_name = user.login_name
            self.email_me = user.email_me
            self.email = user.email
            self.password = user.password
            self.salt = user.salt
            self.phone_number = user.phone_number
            self.authorized = user.authorized
            self.admin = user.admin
        return

    @classmethod
    def get(cls, login_name):
        try:
            return cls(login_name)
        except LookupError:
            return None

    @property
    def is_admin(self):
        return self.admin

    @property
    def is_authorized(self):
        return self.authorized


@login_manager.user_loader
def load_user(login_name):
    return User.get(login_name)


# TODO make this the registration page
@app.route('/login')
def login():
    return '''
        <form action="/login/check" method="post">
            <p>Username: <input name="username" type="text"></p>
            <p>Password: <input name="password" type="password"></p>
            <input type="submit">
        </form>
    '''


@app.route('/login/check', methods=['POST'])
def login_check():
    flask_error_message = "Username or password incorrect"

    form = forms.LoginForm(prefix='login_')
    if form.validate_on_submit():
        login_name = form.login_name.data
        user = User.get(login_name)
        if user:
            if user.is_authorized:
                password = form.password.data
                password = hashlib.sha256(password.encode() + user.salt.encode()).hexdigest()
                if password == user.password:
                    flask_login.login_user(user)
                    logger.debug('Successfully logged in user {}'.format(login_name))
                    flask.flash('Successfully logged in', category='success')
                else:
                    flask.flash(flask_error_message, category='danger')
            else:
                flask.flash('Your account has not yet been authorized. Please bug someone about it.')
        else:
            flask.flash(flask_error_message, category='danger')
    else:
        flask.flash(flask_error_message, category='danger')

    return flask.redirect(flask.url_for('index'))


@app.route('/logout')
def logout():
    if flask_login.current_user.is_authenticated:
        flask_login.logout_user()
        flask.flash('Successfully logged out', category='success')
    return flask.redirect(flask.url_for('index'))


def format_phone_number(phone_number):
    """
    Takes in a phone number and formats it with hyphens
    Can accept 10 or 11 digit numbers
    TODO make the formatter accept different types of numbers

    :param phone_number: string of a US phone number
    :return: a string of a properly formated number
    """
    phone_number = phone_number.replace('-', '')
    phone_number = phone_number.replace(' ', '')
    if len(phone_number) == 10:
        return '-'.join((phone_number[:3], phone_number[3:6], phone_number[6:]))
    elif len(phone_number) == 11:
        return '-'.join((phone_number[0], phone_number[1:4], phone_number[4:7], phone_number[7:]))
    else:
        return phone_number


@app.route('/login/settings', methods=['GET', 'POST'])
def login_settings():
    if flask_login.current_user.is_authenticated:
        form = forms.SettingsForm()
        if flask.request.method == 'POST':
            if form.validate_on_submit():
                name = form.name.data
                email = form.email.data
                phone_number = form.phone_number.data
                phone_number = format_phone_number(phone_number or '')
                email_me = form.email_me.data

                logger.debug('Updating user settings: Login name: {} |Name: {} |email: {} |Phone: {} |email me?: {}'.format(flask_login.current_user.login_name, name, email, phone_number, email_me))

                user = models.User.get(models.User.login_name == flask_login.current_user.login_name)
                user.name = name
                user.email = email
                user.phone_number = format_phone_number(phone_number)
                user.email_me = email_me
                user.save()

                flask.flash('Settings changed successfully', 'success')
                return flask.redirect('/login/settings')
            else:
                # Form not valid
                logger.debug('Invalid form data')
                flask.flash('Invalid data submitted', category='danger')
                name = form.name.data
                email = form.email.data
                phone_number = form.phone_number.data
                email_me = form.email_me.data
        elif flask.request.method == 'GET':
            name = flask_login.current_user.name
            email = flask_login.current_user.email
            phone_number = flask_login.current_user.phone_number
            email_me = flask_login.current_user.email_me

        flask.flash('Phone number currently does nothing')  # TODO fix this
        return flask.render_template('settings.html', form=form, name=name, email=email, phone_number=phone_number, email_me=email_me)
    return flask.redirect(flask.url_for('index'))


@app.route('/login/register', methods=['GET', 'POST'])
def login_register():
    if not flask_login.current_user.is_authenticated:
        form = forms.RegisterForm()
        if flask.request.method == 'POST':
            if form.validate_on_submit():
                login_name = form.login_name.data
                password = form.password.data
                name = form.name.data
                email = form.email.data
                phone_number = form.phone_number.data
                email_me = form.email_me.data

                logger.debug('Registering new user: Login name: {} |Password: {}|Name: {} |email: {} |Phone: {} |email me?: {}'.format(login_name, password, name, email, phone_number, email_me))  # TODO records password in log, remove this

                # Password
                salt = base64.b64encode(os.urandom(32)).decode()
                password = hashlib.sha256(password.encode() + salt.encode()).hexdigest()
                logger.debug('pass hash is {}'.format(password))

                try:
                    models.User(name=name,
                                login_name=login_name,
                                salt=salt,
                                password=password,
                                email_me=email_me,
                                email=email).save()
                except peewee.IntegrityError as e:
                    logger.debug(e)
                    problem_field = str(e)[str(e).find('.')+1:]

                    if problem_field in form.__dict__:
                        logger.debug('Problem was {}'.format(problem_field))
                        getattr(form, problem_field).errors.append('This entry already exists, please choose a new one')
                    else:
                        raise e
                else:
                    flask.flash('Successfully made account', category='success')
                    return flask.redirect(flask.url_for('index'))
        elif flask.request.method == 'GET':
            flask.flash('Phone number currently does nothing')  # TODO fix this
        return flask.render_template('register.html', form=form)
    else:  # The user is authenticated
        return flask.redirect(flask.url_for('index'))
