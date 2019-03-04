from greenzora import server_app

from flask import current_app
from flask_login import current_user
from functools import wraps


def is_debug():
    return server_app.config['DEBUG']


# This function overwrites the login_required decorator of flask_login. It gives us the ability to distinguish between
# normal users that can only annotate and admins that may change settings and create new users.
def login_required(required_role='any'):
    def wrapper(fn):
        @wraps(fn)
        def inner_fn(*args, **kwargs):
            if not current_user.is_authenticated():
                return current_app.login_manager.unauthorized()
            user_role = current_app.login_manager.reload_user().get_user_role()
            if (required_role != 'any') and (user_role != required_role):
                return current_app.login_manager.unauthorized
            return fn(*args, **kwargs)
        return inner_fn
    return wrapper
