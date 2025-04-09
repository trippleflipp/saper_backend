from flask import Blueprint, request, jsonify
from app import db, bcrypt
from app.models import User
from app.utils.auth import token_required
from app.utils.email import generate_verification_code, send_verification
from app.utils.token import generate_token

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    username = data.get('username')
    password = data.get('password')
    email = data.get('email')

    if not username or not password or not email:
        return jsonify({'message': 'Username, password, and email are required'}), 400

    # Validate email format
    if '@' not in email or '.' not in email:
        return jsonify({'message': 'Invalid email format'}), 400

    # Check if username or email already exists
    existing_user_username = User.query.filter(User.username == username).first()
    existing_user_email = User.query.filter(User.email == email).first()

    if existing_user_username or existing_user_email:
        return jsonify({'message': 'Username already exists'}), 400

    # Generate verification code and store it
    verification_code = generate_verification_code()

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(username=username, password=hashed_password, email=email, verification_code=verification_code, is_verified=False)

    db.session.add(new_user)
    db.session.commit()

    # Send verification email
    if send_verification(email, verification_code):
        return jsonify({'message': 'Please check your email for verification.'}), 201
    else:
        # Rollback the user creation if email failed to send
        db.session.delete(new_user)
        db.session.commit()
        return jsonify({'message': 'Registration failed: Error sending verification email'}), 500


@auth_bp.route('/verify_email', methods=['POST'])
def verify_email():
    data = request.get_json()
    email = data.get('email')
    code = data.get('code')

    if not email or not code:
        return jsonify({'message': 'Email and verification code are required'}), 400

    user = User.query.filter(User.email == email).first()

    if not user:
        return jsonify({'message': 'User not found'}), 404

    if user.is_verified:
        return jsonify({'message': 'Email already verified'}), 400

    if user.verification_code == code:
        user.is_verified = True
        user.verification_code = None
        db.session.commit()
        return jsonify({'message': 'Email verified successfully'}), 200
    else:
        return jsonify({'message': 'Invalid verification code'}), 400


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Username and password are required'}), 400

    user = User.query.filter_by(username=username).first()

    if not user or not bcrypt.check_password_hash(user.password, password):
        return jsonify({'message': 'Invalid username or password'}), 401

    if not user.is_verified:
        return jsonify({'message': 'Please verify your email before logging in'}), 403

    token = generate_token(user)
    return jsonify({'access_token': token}), 200


@auth_bp.route('/protected', methods=['GET'])
@token_required
def protected(current_user):
    return jsonify({'message': f'Hello, {current_user.username}! You have access to this protected resource.', 'user': current_user.to_dict()}), 200


@auth_bp.route('/request_password_reset', methods=['POST'])
def request_password_reset():
    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({'message': 'Email is required'}), 400

    user = User.query.filter(User.email == email).first()

    if not user:
        return jsonify({'message': 'User not found'}), 404

    # Генерируем новый код подтверждения
    verification_code = generate_verification_code()
    user.verification_code = verification_code
    db.session.commit()

    # Отправляем код на почту
    if send_verification(email, verification_code):
        return jsonify({'message': 'Password reset code has been sent to your email'}), 200
    else:
        return jsonify({'message': 'Error sending verification email'}), 500


@auth_bp.route('/reset_password', methods=['POST'])
def reset_password():
    data = request.get_json()
    email = data.get('email')
    code = data.get('code')
    new_password = data.get('new_password')

    if not email or not code or not new_password:
        return jsonify({'message': 'Email, verification code and new password are required'}), 400

    user = User.query.filter(User.email == email).first()

    if not user:
        return jsonify({'message': 'User not found'}), 404

    if user.verification_code != code:
        return jsonify({'message': 'Invalid verification code'}), 400

    # Хешируем новый пароль и сохраняем его
    hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
    user.password = hashed_password
    user.verification_code = None  # Очищаем код подтверждения
    db.session.commit()

    return jsonify({'message': 'Password has been reset successfully'}), 200 