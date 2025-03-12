from flask import Flask, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, JWTManager, get_jwt_identity, get_jwt
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from passlib.hash import sha256_crypt
from config import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME


app = Flask(__name__)
CORS(app=app)
app.config['JWT_SECRET_KEY'] = 'secret'
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


jwt = JWTManager(app)
db = SQLAlchemy(app)
tables_created = False


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), default='player')

    def __init__(self, username, password, role='player'):
        self.username = username
        self.password = sha256_crypt.encrypt(password)
        self.role = role

    def verify_password(self, password):
        print(password, self.password)
        return sha256_crypt.verify(password, self.password)

    def get_id(self):
        return str(self.id)


@app.before_request
def before_request():
    global tables_created
    if not tables_created:
        with app.app_context():
            db.create_all()
        tables_created = True


@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    print(data)
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Username and password are required'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'message': 'Username already exists'}), 400

    new_user = User(username=username, password=password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User created successfully'}), 201


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()

    if user and user.verify_password(password):
        access_token = create_access_token(identity=user.id, additional_claims={'role': user.role})
        return jsonify({'access_token': access_token}), 200
    else:
        return jsonify({'message': 'Invalid credentials'}), 401


@app.route('/admin', methods=['GET'])
@jwt_required()
def admin_route():
    claims = get_jwt()
    if claims['role'] == 'admin':
        return jsonify({'message': 'Admin area'}), 200
    else:
        return jsonify({'message': 'Unauthorized'}), 403


@app.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    return jsonify({'message': f'Hello, {user.username}! Your role is: {user.role}'}), 200


if __name__ == '__main__':
    app.run(debug=True)