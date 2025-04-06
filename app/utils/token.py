import datetime
import jwt
from flask import current_app

def generate_token(user):
    payload = {
        'id': user.id,
        'username': user.username,
        'role': user.role,
        'exp': datetime.datetime.now() + datetime.timedelta(minutes=60)
    }
    token = jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')
    return token


def verify_token(token):
    try:
        payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return 'Token has expired'
    except jwt.InvalidTokenError:
        return 'Invalid token'
    except Exception as e:
        print(f"Error decoding token: {e}")
        return 'Invalid token' 