from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import jwt
from flask_cors import CORS
import datetime
from functools import wraps
from config import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME
import enum

app = Flask(__name__)
CORS(app=app)
app.config['SECRET_KEY'] = 'secret'
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# --- Database Model ---

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)  # Store hashed passwords
    role = db.Column(db.String(20), default='player')

    def __repr__(self):
        return f"User('{self.username}', '{self.role}')"

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role
        }
    
class Difficulty(enum.Enum):
    easy = 'easy'
    medium = 'medium'
    hard = 'hard'

class Leaderboard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now())
    milliseconds = db.Column(db.Integer, nullable=False)
    username = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    difficulty = db.Column(db.Enum(Difficulty), nullable=False)

    user = db.relationship('User', backref=db.backref('leaderboard_entries', lazy=True))

    def __repr__(self):
        return f"Leaderboard(user_id={self.user_id}, milliseconds={self.milliseconds}, difficulty={self.difficulty})"
    
    def to_dict(self):
        return {
            'id': self.id,
            'created_at': self.created_at.isoformat(),
            'milliseconds': self.milliseconds,
            'username': self.username,
            'user_id': self.user_id,
            'difficulty': self.difficulty.value
        }


# --- Utility Functions ---

def generate_token(user):
    payload = {
        'id': user.id,
        'username': user.username,
        'role': user.role,
        'exp': datetime.datetime.now() + datetime.timedelta(minutes=60)
    }
    token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
    return token


def verify_token(token):
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return 'Token has expired'
    except jwt.InvalidTokenError:
        return 'Invalid token'
    except Exception as e:
        print(f"Error decoding token: {e}")
        return 'Invalid token'


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        print(request)
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            data = verify_token(token)
            if isinstance(data, str):  # Error message from verify_token
                return jsonify({'message': data}), 401  # Return the error message

            current_user = User.query.filter_by(id=data['id']).first()

        except:
            return jsonify({'message': 'Token is invalid!'}), 401

        return f(current_user, *args, **kwargs)  # Pass the user to the decorated function

    return decorated


def admin_required(f):
    @wraps(f)
    @token_required
    def decorated(current_user, *args, **kwargs):
        if current_user.role != 'admin':
            return jsonify({'message': 'Cannot perform that function!'}), 403  # Forbidden

        return f(current_user, *args, **kwargs)

    return decorated



# --- API Endpoints ---

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Username and password are required'}), 400

    # Check if username or email already exists
    existing_user = User.query.filter((User.username == username)).first()
    if existing_user:
        return jsonify({'message': 'Username already exists'}), 400


    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(username=username, password=hashed_password)

    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'Registered successfully'}), 201


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Username and password are required'}), 400

    user = User.query.filter_by(username=username).first()

    if not user or not bcrypt.check_password_hash(user.password, password):
        return jsonify({'message': 'Invalid username or password'}), 401

    token = generate_token(user)
    return jsonify({'access_token': token}), 200


@app.route('/protected', methods=['GET'])
@token_required
def protected(current_user):
    return jsonify({'message': f'Hello, {current_user.username}! You have access to this protected resource.', 'user': current_user.to_dict()}), 200


@app.route("/new_record", methods=['POST'])
@token_required
def new_record(current_user):
    data = request.get_json()
    try:
        milliseconds = int(data.get('milliseconds'))
        difficulty_str = data.get('difficulty')
        difficulty = Difficulty(difficulty_str.lower())
    except (ValueError, KeyError):
        return jsonify({'message': 'Invalid data.  Requires: milliseconds (integer), difficulty (easy, medium, hard)'}), 400

    new_record = Leaderboard(
        milliseconds=milliseconds,
        username=current_user.username,
        user_id=current_user.id,
        difficulty=difficulty
    )

    db.session.add(new_record)
    db.session.commit()  

    top_10 = Leaderboard.query.filter_by(difficulty=difficulty).order_by(Leaderboard.milliseconds.asc()).limit(10).all()

    if len(top_10) < 10 or milliseconds < top_10[-1].milliseconds:
        all_records = Leaderboard.query.filter_by(difficulty=difficulty).order_by(Leaderboard.milliseconds.asc()).all()
        if len(all_records) > 10:
             record_to_remove = all_records[-1]
             db.session.delete(record_to_remove)
             db.session.commit()

        return jsonify({'message': 'New record submitted and is in the top 10!', 'record_id': new_record.id}), 201

    else:
        db.session.delete(new_record)
        db.session.commit()
        return jsonify({'message': 'New record submitted, but it is not in the top 10.'}), 200
    

@app.route("/get_records", methods=['GET'])
def get_records():
    all_results = {}
    for difficulty in Difficulty:
        top_10 = Leaderboard.query.filter_by(difficulty=difficulty).order_by(Leaderboard.milliseconds.asc()).limit(10).all()
        all_results[difficulty.value] = [record.to_dict() for record in top_10]

    return jsonify(all_results), 200

@app.route('/admin', methods=['GET'])
@admin_required
def admin(current_user):
    return jsonify({'message': f'Hello, {current_user.username}! You have access to the admin panel.'}), 200


@app.route('/users', methods=['GET'])
@admin_required
def get_all_users(current_user):
    users = User.query.all()
    user_list = [user.to_dict() for user in users]
    return jsonify({'users': user_list}), 200


# --- Main ---

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables
    app.run(debug=True)