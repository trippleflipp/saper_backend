import enum
from app import db

class Difficulty(enum.Enum):
    easy = 'easy'
    medium = 'medium'
    hard = 'hard'

class Leaderboard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime)
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