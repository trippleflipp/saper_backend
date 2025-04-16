from flask import Blueprint, request, jsonify, send_file
from app import db, bcrypt
from app.models import User
import pyqrcode
import onetimepass
from io import BytesIO
from app.utils.auth import token_required, generate_secret
from app.utils.email import generate_verification_code, send_verification
from app.utils.token import generate_token


auth_bp = Blueprint('auth', __name__)


# BASE AUTH ROUTES
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


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    username = data.get('username')
    password = data.get('password')
    email = data.get('email')

    if not username or not password or not email:
        return jsonify({'message': 'Username, password, and email are required'}), 400

    if '@' not in email or '.' not in email:
        return jsonify({'message': 'Invalid email format'}), 400

    existing_user_username = User.query.filter(User.username == username).first()
    existing_user_email = User.query.filter(User.email == email).first()

    if existing_user_username or existing_user_email:
        return jsonify({'message': 'Username already exists'}), 400

    verification_code = generate_verification_code()

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(username=username, password=hashed_password, email=email, verification_code=verification_code, is_verified=False)

    db.session.add(new_user)
    db.session.commit()

    if send_verification(email, verification_code):
        return jsonify({'message': 'Please check your email for verification.'}), 201
    else:
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


# RESET ROUTES
@auth_bp.route('/request_password_reset', methods=['POST'])
def request_password_reset():
    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({'message': 'Email is required'}), 400

    user = User.query.filter(User.email == email).first()

    if not user:
        return jsonify({'message': 'User not found'}), 404

    verification_code = generate_verification_code()
    user.verification_code = verification_code
    db.session.commit()

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

    hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
    user.password = hashed_password
    user.verification_code = None
    db.session.commit()

    return jsonify({'message': 'Password has been reset successfully'}), 200


# 2FA ROUTES
@auth_bp.route('/enable_2fa', methods=['GET'])
@token_required
def enable_2fa(current_user):
    try:
        current_user.enabled_2fa = True
        db.session.commit()

        return jsonify({ 'message': '2fa enabled' }), 200
    except Exception as err:
        return jsonify({ 'message': f'{err}' }), 400


@auth_bp.route('/disable_2fa', methods=['GET'])
@token_required
def disable_2fa(current_user):
    try:
        current_user.secret_2fa = None
        current_user.enabled_2fa = False
        db.session.commit()

        return jsonify({ 'message': '2fa disabled' }), 200
    except Exception as err:
        return jsonify({ 'message': f'{err}' }), 400


@auth_bp.route('/generate_qr', methods=['GET'])
@token_required
def generate_qr(current_user):
    try:
        secret = generate_secret()
        current_user.secret_2fa = secret
        otp_uri = f"otpauth://totp/Saper2fa:{current_user.email}?secret={secret}&issuer=Saper2fa"
        qr_code = pyqrcode.create(otp_uri)

        buffer = BytesIO()
        qr_code.png(buffer, scale=8)
        buffer.seek(0)
        db.session.commit()

        return send_file(buffer, mimetype='image/png')
    except Exception as err:
        return jsonify({ 'message': f'{err}' }), 400


@auth_bp.route('/verify_2fa', methods=['POST'])
@token_required
def verify_2fa(current_user):
    otp = request.get_json()['otp']

    try:
        if onetimepass.valid_totp(otp, current_user.secret_2fa):
            return jsonify({ 'message': 'Success' }), 200
    except Exception as err:
        return jsonify({ 'message': f'{err}' }), 400