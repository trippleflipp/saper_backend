from flask import Blueprint, request, jsonify
import datetime
from app import db
from app.models import Leaderboard, Difficulty
from app.utils.auth import token_required


game_bp = Blueprint('game', __name__)


@game_bp.route("/new_record", methods=['POST'])
@token_required
def new_record(current_user):
    data = request.get_json()
    try:
        milliseconds = int(data.get('milliseconds'))
        difficulty_str = data.get('difficulty')
        difficulty = Difficulty(difficulty_str.lower())
    except (ValueError, KeyError):
        return jsonify({'message': 'Invalid data. Requires: milliseconds (integer), difficulty (easy, medium, hard)'}), 400

    if not current_user.is_verified:
        return jsonify({'message': 'User is not verified'}), 400

    existing_record = Leaderboard.query.filter_by(
        user_id=current_user.id,
        difficulty=difficulty
    ).first()

    if existing_record:
        if milliseconds < existing_record.milliseconds:
            existing_record.milliseconds = milliseconds
            existing_record.created_at = datetime.datetime.now()
            db.session.commit()
            current_user.coins += 15
            db.session.commit()
        else:
            return jsonify({'message': 'New record submitted, but it is not in the top 10.'}), 200
    else:
        new_record = Leaderboard(
            created_at=datetime.datetime.now(),
            milliseconds=milliseconds,
            username=current_user.username,
            user_id=current_user.id,
            difficulty=difficulty
        )
        db.session.add(new_record)
        db.session.commit()
        current_user.coins += 15
        db.session.commit()

    top_10 = Leaderboard.query.filter_by(difficulty=difficulty).order_by(Leaderboard.milliseconds.asc()).limit(10).all()

    if len(top_10) < 10 or milliseconds < top_10[-1].milliseconds:
        all_records = Leaderboard.query.filter_by(difficulty=difficulty).order_by(Leaderboard.milliseconds.asc()).all()
        if len(all_records) > 10:
            record_to_remove = all_records[-1]
            db.session.delete(record_to_remove)
            db.session.commit()
        
        current_user.coins += 985
        db.session.commit()

        return jsonify({'message': 'New record submitted and is in the top 10!'}), 201
    else:
        return jsonify({'message': 'New record submitted, but it is not in the top 10.'}), 200


@game_bp.route("/get_records", methods=['GET'])
def get_records():
    all_results = {}
    for difficulty in Difficulty:
        top_10 = Leaderboard.query.filter_by(difficulty=difficulty).order_by(Leaderboard.milliseconds.asc()).limit(11).all()
        all_results[difficulty.value] = [record.to_dict() for record in top_10]

    return jsonify(all_results), 200


@game_bp.route("/get_personal_records", methods=['GET'])
@token_required
def get_personal_records(current_user):
    records_list = []
    records = Leaderboard.query.filter_by(user_id=current_user.id).all()
    for record in records:
        records_list.append({
            'milliseconds': record.milliseconds,
            'difficulty': record.difficulty.value
        })

    return jsonify(records_list), 200


@game_bp.route("/open_mine", methods=['GET'])
@token_required
def open_mine(current_user):
    try:
        if current_user.coins >= 10:
            current_user.coins -= 10
            db.session.commit()
            return jsonify({"message": "ok"}), 201
        else: 
            return jsonify({"message": "neok"}), 200
    except Exception as err:
        return jsonify({"error": err}), 400
    

@game_bp.route("/get_coins", methods=['GET'])
@token_required
def get_coins(current_user):
    try:
        return jsonify({"coins": current_user.coins}), 200
    except Exception as err:
        return jsonify({"error": err}), 400 
    
@game_bp.route("/get_available_bg", methods=['GET'])
@token_required
def get_available_bg(current_user):
    try:
        return jsonify({"available_bg": current_user.available_bg}), 200
    except Exception as err:
        return jsonify({"error": err}), 400
    
@game_bp.route("/add_bg", methods=['POST'])
@token_required
def add_bg(current_user, bg):
    try:
        current_user.available_bg += f"{bg.id},"
        current_user.coins -= bg.price
        db.session.commit()
        return jsonify({"message": "ok"}), 201
    except Exception as err:
        return jsonify({"error": err}), 400
        
        
