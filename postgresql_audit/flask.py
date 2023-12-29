from contextlib import contextmanager
from copy import copy

from flask import g, request

from .audit_logger import AuditLogger


def default_actor_id():
    from flask_login import current_user

    try:
        return current_user.id
    except AttributeError:
        return

def default_client_addr():
    # Return None if we are outside of request context.
    return (request and request.remote_addr) or None

def merge_dicts(a, b):
    c = copy(a)
    c.update(b)
    return c


@contextmanager
def activity_values(**values):
    if not g:
        yield  # Needed for contextmanager
        return
    if hasattr(g, 'activity_values'):
        previous_value = g.activity_values
        values = merge_dicts(previous_value, values)
    else:
        previous_value = None
    g.activity_values = values
    yield
    if previous_value is None:
        del g.activity_values
    else:
        g.activity_values = previous_value


audit_logger = AuditLogger()
