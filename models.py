from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True,
                         nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)

    # Profile information
    display_name = db.Column(db.String(100))
    bio = db.Column(db.Text)
    avatar = db.Column(
        db.String(200), default='/static/images/default-avatar.jpg')
    wallpaper = db.Column(
        db.String(200), default='/static/images/default-wallpaper.jpg')
    location = db.Column(db.String(100))
    website = db.Column(db.String(200))
    birth_date = db.Column(db.Date)

    # Account status - Approval & Verification
    # Admin approval (profile visible)
    is_approved = db.Column(db.Boolean, default=False)
    is_verified = db.Column(db.Boolean, default=False)  # Identity verified
    is_featured = db.Column(db.Boolean, default=False)  # Featured on homepage
    is_admin = db.Column(db.Boolean, default=False)      # Admin privileges
    # Account active/inactive
    is_active = db.Column(db.Boolean, default=True)
    is_flagged = db.Column(db.Boolean, default=False)    # Flagged for review
    # Rejected applications
    is_rejected = db.Column(db.Boolean, default=False)

    # Restriction fields (NEW)
    # Account is restricted
    is_restricted = db.Column(db.Boolean, default=False)
    restriction_reason = db.Column(db.String(100))        # Why restricted
    restriction_duration = db.Column(
        db.String(20))       # 24h, 7d, 30d, permanent
    restriction_notes = db.Column(db.Text)                # Admin notes
    restricted_at = db.Column(db.DateTime)                # When restricted
    restricted_by = db.Column(db.Integer, db.ForeignKey(
        'users.id'))  # Admin who restricted
    restriction_lifted_at = db.Column(db.DateTime)        # When lifted
    restriction_lifted_by = db.Column(
        db.Integer, db.ForeignKey('users.id'))  # Admin who lifted

    # Stats
    followers_count = db.Column(db.Integer, default=0)
    views_count = db.Column(db.Integer, default=0)
    likes_count = db.Column(db.Integer, default=0)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    social_links = db.relationship(
        'SocialLink', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    gallery_images = db.relationship(
        'GalleryImage', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    posts = db.relationship('Post', backref='author',
                            lazy='dynamic', cascade='all, delete-orphan')
    comments = db.relationship(
        'Comment', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    followers = db.relationship('Follow', foreign_keys='Follow.followed_id',
                                backref='followed', lazy='dynamic', cascade='all, delete-orphan')
    following = db.relationship('Follow', foreign_keys='Follow.follower_id',
                                backref='follower', lazy='dynamic', cascade='all, delete-orphan')

    # Admin relationships
    restricted_by_user = db.relationship(
        'User', foreign_keys=[restricted_by], remote_side=[id])
    restriction_lifted_by_user = db.relationship(
        'User', foreign_keys=[restriction_lifted_by], remote_side=[id])

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return str(self.id)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'display_name': self.display_name or self.username,
            'avatar': self.avatar,
            'wallpaper': self.wallpaper,
            'bio': self.bio,
            'is_verified': self.is_verified,
            'is_featured': self.is_featured,
            'is_approved': self.is_approved,
            'is_restricted': self.is_restricted,
            'followers': self.followers_count,
            'views': self.views_count,
            'likes': self.likes_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None
        }

    def __repr__(self):
        return f'<User {self.username}>'


class SocialLink(db.Model):
    __tablename__ = 'social_links'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    # twitter, instagram, onlyfans, etc.
    platform = db.Column(db.String(50), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    handle = db.Column(db.String(100))
    # True for OnlyFans, Fansly, etc.
    is_premium = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<SocialLink {self.platform}:{self.handle}>'


class GalleryImage(db.Model):
    __tablename__ = 'gallery_images'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    media_url = db.Column(db.String(500), nullable=False)  # URL to media file
    thumbnail_url = db.Column(db.String(500))  # For video thumbnails
    caption = db.Column(db.String(200))
    # 'image' or 'video'
    media_type = db.Column(db.String(20), default='image')
    file_size = db.Column(db.Integer)  # Size in bytes
    duration = db.Column(db.Integer)  # Video duration in seconds (for videos)
    is_public = db.Column(db.Boolean, default=True)
    likes = db.Column(db.Integer, default=0)
    views = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<GalleryMedia {self.id} - {self.media_type}>'


class Post(db.Model):
    __tablename__ = 'posts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    media_url = db.Column(db.String(500))
    media_type = db.Column(db.String(20))  # 'image', 'video'
    likes = db.Column(db.Integer, default=0)
    views = db.Column(db.Integer, default=0)
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    comments = db.relationship(
        'Comment', backref='post', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Post {self.id}>'


class Comment(db.Model):
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Comment {self.id}>'


class Follow(db.Model):
    __tablename__ = 'follows'

    id = db.Column(db.Integer, primary_key=True)
    follower_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=False)
    followed_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('follower_id', 'followed_id',
                            name='unique_follow'),
    )

    def __repr__(self):
        return f'<Follow {self.follower_id}->{self.followed_id}>'


class VerificationRequest(db.Model):
    __tablename__ = 'verification_requests'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    id_proof = db.Column(db.String(500))  # Path to ID document
    selfie = db.Column(db.String(500))  # Path to selfie with ID
    # pending, approved, rejected
    status = db.Column(db.String(20), default='pending')
    admin_notes = db.Column(db.Text)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __repr__(self):
        return f'<VerificationRequest {self.user_id}>'


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    # follow, like, comment, verification, approval, restriction, etc.
    type = db.Column(db.String(50))
    message = db.Column(db.Text)
    link = db.Column(db.String(500))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Notification {self.id}>'


class AdminLog(db.Model):
    __tablename__ = 'admin_logs'

    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    # approve, restrict, delete, etc.
    action = db.Column(db.String(100), nullable=False)
    target_id = db.Column(db.Integer)  # ID of affected user
    # user, post, comment, etc.
    target_type = db.Column(db.String(50), default='user')
    details = db.Column(db.Text)  # JSON string with additional details
    ip_address = db.Column(db.String(50))  # Admin IP for audit
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    admin = db.relationship('User', foreign_keys=[admin_id])

    def __repr__(self):
        return f'<AdminLog {self.action} by {self.admin_id} at {self.timestamp}>'

