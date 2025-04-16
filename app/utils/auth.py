from functools import wraps
from flask import request, jsonify
from app.models import User
from app.utils.token import verify_token
import base64
import os


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            data = verify_token(token)
            if isinstance(data, str):
                return jsonify({'message': data}), 401

            current_user = User.query.filter_by(id=data['id']).first()

        except:
            return jsonify({'message': 'Token is invalid!'}), 401

        return f(current_user, *args, **kwargs)

    return decorated


def admin_required(f):
    @wraps(f)
    @token_required
    def decorated(current_user, *args, **kwargs):
        if current_user.role != 'admin':
            return jsonify({'message': 'Cannot perform that function!'}), 403

        return f(current_user, *args, **kwargs)

    return decorated


def generate_secret():
    return base64.b32encode(os.urandom(10)).decode('utf-8')