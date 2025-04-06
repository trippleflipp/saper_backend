from app import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    role = db.Column(db.String(20), default='player')
    coins = db.Column(db.Integer, nullable=False, default=10)
    email = db.Column(db.String(120), unique=True, nullable=False)
    verification_code = db.Column(db.String(6), nullable=True)
    is_verified = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"User('{self.username}', '{self.role}')"

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role,
            'coins': self.coins,
            'email': self.email,
            'verification_code': self.verification_code,
            'is_verified': self.is_verified,
        } 