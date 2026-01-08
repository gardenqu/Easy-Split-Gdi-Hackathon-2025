from functools import wraps
from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import User


def role_required(role_name):
    """Decorator to restrict access based on user role"""
    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            user = User.query.get(get_jwt_identity())
            if not user:
                return jsonify({'msg': 'User not found'}), 404
            user_roles = [r.name for r in user.roles]  # fixed
            if role_name not in user_roles:
                return jsonify({'msg': 'Access forbidden: insufficient permissions'}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator
