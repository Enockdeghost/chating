from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    bio = db.Column(db.String(500))
    avatar_url = db.Column(db.String(200))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Add these relationships
    groups = db.relationship('GroupChat', secondary='group_member', 
                           backref=db.backref('user_members', lazy='dynamic'))

class PrivateMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

class GroupChat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200))
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_group_admin'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    members = db.relationship('GroupMember', backref='group', lazy=True)
    messages = db.relationship('GroupMessage', backref='group', lazy=True)
    admin = db.relationship('User', foreign_keys=[admin_id], backref='administered_groups')

class GroupMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group_chat.id', name='fk_message_group'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_message_sender'), nullable=False)
    content = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Add relationship to sender
    sender = db.relationship('User', backref='group_messages')

class GroupMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group_chat.id', name='fk_member_group'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_member_user'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Add relationship to user
    user = db.relationship('User', backref='group_memberships')

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.String(500), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # 'admin', 'chat', 'group'
    is_read = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
