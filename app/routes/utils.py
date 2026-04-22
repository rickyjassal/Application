from functools import wraps

from flask import jsonify, session


def api_login_required(view_func):
    """Require an authenticated admin session for JSON API routes."""

    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Authentication required'}), 401
        return view_func(*args, **kwargs)

    return wrapped
