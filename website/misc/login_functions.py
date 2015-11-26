import flask
import logging
import flask_login
import peewee
import flask_login
import hashlib
import os
import base64

from __init__ import app
import models

logger = logging.getLogger(__name__)

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


func_dict = {56: hashlib.sha224,
             64: hashlib.sha256,
             96: hashlib.sha384,
             128: hashlib.sha512}
try:
    hash_func = func_dict[models.User.password.max_length]
    logger.critical('Selected hash function {}'.format(hash_func))
except KeyError:
    logger.critical('Unable to select proper hash algorithm, falling back to hash256')
    hash_func = hashlib.sha256


def get_password_hash(password, salt):
    """Generate the password hash given the plaintext of the password anda salt"""
    return hash_func(password.encode() + salt.encode()).hexdigest()


def gen_password(password):
    """Generate a password hash given the plaintext of the password"""
    salt = base64.b64encode(os.urandom(models.User.salt.max_length)).decode()
    password = get_password_hash(password, salt)
    return password, salt
