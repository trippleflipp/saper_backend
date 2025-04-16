from flask import Blueprint, jsonify
from app.models import User
from app.utils.auth import admin_required


admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/admin', methods=['GET'])
@admin_required
def admin(current_user):
    return jsonify({'message': f'Hello, {current_user.username}! You have access to the admin panel.'}), 200


@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_all_users(current_user):
    users = User.query.all()
    user_list = [user.to_dict() for user in users]
    return jsonify({'users': user_list}), 200 