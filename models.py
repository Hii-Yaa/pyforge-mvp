from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import bcrypt

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User model for authentication and game ownership."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to games
    games = db.relationship('Game', backref='uploader', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        """Hash and set the user's password."""
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def check_password(self, password):
        """Verify password against stored hash."""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

    def __repr__(self):
        return f'<User {self.username}>'


class Game(db.Model):
    """Game model for uploaded game files and metadata."""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    filename = db.Column(db.String(255), nullable=False)  # Stored file name
    uploader_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to comments
    comments = db.relationship('Comment', backref='game', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Game {self.title}>'


class Comment(db.Model):
    """Comment model for game comments and replies."""
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    tag = db.Column(db.String(20), nullable=True)  # Tag: feedback, bug, request, discussion, hidden, or None
    original_tag = db.Column(db.String(20), nullable=True)  # Stores tag before hidden
    hidden_at = db.Column(db.DateTime, nullable=True)  # Timestamp when tagged as hidden
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Null for guests
    guest_name = db.Column(db.String(50), default='guest')
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)  # Self-referential for replies
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    author = db.relationship('User', backref='comments', lazy=True)
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Comment {self.id} on Game {self.game_id}>'


class CommentTagHistory(db.Model):
    """History of comment tag changes."""
    id = db.Column(db.Integer, primary_key=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=False)
    old_tag = db.Column(db.String(20), nullable=True)
    new_tag = db.Column(db.String(20), nullable=True)
    changed_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Null for system
    changed_by = db.Column(db.String(50), default='system')  # 'system' or user ID
    changed_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    comment = db.relationship('Comment', backref='tag_history', lazy=True)

    def __repr__(self):
        return f'<TagHistory {self.comment_id}: {self.old_tag} -> {self.new_tag}>'
