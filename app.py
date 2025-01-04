from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Response, stream_with_context
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, PrivateMessage, GroupChat, GroupMessage, GroupMember, Notification
from forms import SignUpForm, LoginForm, MessageForm, GroupChatForm, ProfileForm
from datetime import datetime, timedelta
import os
from werkzeug.utils import secure_filename
from wtforms.validators import DataRequired, Email, Length, EqualTo
from sqlalchemy import or_
import json
import time
from flask import session

app = Flask(__name__, static_url_path='/static')
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ONLINE_LAST_SEEN_TIMEOUT = 300  # 5 minutes in seconds

# Helper functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_user_online(user):
    if not user.last_seen:
        return False
    return datetime.utcnow() - user.last_seen < timedelta(seconds=ONLINE_LAST_SEEN_TIMEOUT)

# User loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Before request
@app.before_request
def update_last_seen():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('chat_dashboard'))
    return redirect(url_for('login'))

# ... (keep your existing routes)

@app.route('/search/users')
@login_required
def search_users():
    query = request.args.get('q', '').strip()
    if query:
        users = User.query.filter(
            User.username.ilike(f'%{query}%'),
            User.id != current_user.id
        ).all()
        return jsonify([{
            'id': user.id,
            'username': user.username,
            'avatar': url_for('static', filename=user.avatar_url) if user.avatar_url else None,
            'online': is_user_online(user)
        } for user in users])
    return jsonify([])

@app.route('/group/create', methods=['POST'])
@login_required
def create_group():
    data = request.json
    if not data.get('name'):
        return jsonify({'success': False, 'error': 'Group name is required'}), 400
    
    group = GroupChat(
        name=data['name'],
        description=data.get('description', ''),
        admin_id=current_user.id
    )
    db.session.add(group)
    
    # Add current user as member
    member = GroupMember(group=group, user_id=current_user.id)
    db.session.add(member)
    
    # Add other members
    for user_id in data.get('members', []):
        if user_id != current_user.id:
            member = GroupMember(group=group, user_id=user_id)
            db.session.add(member)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'group': {
            'id': group.id,
            'name': group.name,
            'description': group.description
        }
    })

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('chat_dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('chat_dashboard'))
        flash('Invalid email or password')
        return redirect(url_for('login'))
    
    return render_template('login.html', form=form)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('chat_dashboard'))
    
    form = SignUpForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            flash('Email already registered')
            return redirect(url_for('signup'))
        
        hashed_password = generate_password_hash(form.password.data)
        new_user = User(
            username=form.username.data,
            email=form.email.data,
            password=hashed_password
        )
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful!')
        return redirect(url_for('login'))
    
    return render_template('signup.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/chat/dashboard')
@login_required
def chat_dashboard():
    # Get all users except current user
    users = User.query.filter(User.id != current_user.id).all()
    
    # Get user's groups
    groups = GroupChat.query.filter(
        GroupChat.members.any(id=current_user.id)
    ).all()
    
    # Get notifications
    notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).all()
    
    # Get recent chats (both private and group)
    recent_chats = []
    
    # Add private chats
    for user in users:
        last_message = PrivateMessage.query.filter(
            ((PrivateMessage.sender_id == current_user.id) & (PrivateMessage.receiver_id == user.id)) |
            ((PrivateMessage.sender_id == user.id) & (PrivateMessage.receiver_id == current_user.id))
        ).order_by(PrivateMessage.timestamp.desc()).first()
        
        if last_message:
            recent_chats.append({
                'id': f'user_{user.id}',
                'name': user.username,
                'avatar': url_for('static', filename=user.avatar_url) if user.avatar_url else None,
                'last_message': last_message.content,
                'time': last_message.timestamp.strftime('%H:%M'),
                'unread': PrivateMessage.query.filter_by(
                    sender_id=user.id,
                    receiver_id=current_user.id,
                    is_read=False
                ).count(),
                'online': is_user_online(user),
                'type': 'private'
            })
    
    # Add group chats
    for group in groups:
        last_message = GroupMessage.query.filter_by(
            group_id=group.id
        ).order_by(GroupMessage.timestamp.desc()).first()
        
        if last_message:
            recent_chats.append({
                'id': f'group_{group.id}',
                'name': group.name,
                'avatar': None,  # You can add group avatar feature
                'last_message': last_message.content,
                'time': last_message.timestamp.strftime('%H:%M'),
                'unread': GroupMessage.query.filter(
                    GroupMessage.group_id == group.id,
                    GroupMessage.timestamp > last_message.timestamp
                ).count(),
                'type': 'group'
            })
    
    # Sort chats by last message time
    recent_chats.sort(key=lambda x: x['time'], reverse=True)
    
    # Initialize empty chat area
    current_chat = {
        'id': None,
        'name': 'Select a chat',
        'avatar': None,
        'online': False,
        'type': None
    }
    
    messages = []
    
    return render_template('chat_dashboard.html',
                         users=users,
                         groups=groups,
                         notifications=notifications,
                         chats=recent_chats,
                         current_chat=current_chat,
                         messages=messages)

@app.route('/profile')
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    return render_template('profile.html', form=form)

@app.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    form = ProfileForm()
    if form.validate_on_submit():
        if form.avatar.data:
            file = form.avatar.data
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                current_user.avatar_url = f'uploads/{filename}'
        
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.bio = form.bio.data
        
        if form.new_password.data:
            if check_password_hash(current_user.password, form.current_password.data):
                current_user.password = generate_password_hash(form.new_password.data)
            else:
                flash('Current password is incorrect')
                return redirect(url_for('profile'))
        
        db.session.commit()
        flash('Profile updated successfully!')
        
    return redirect(url_for('profile'))

@app.route('/user/<int:user_id>')
@login_required
def view_profile(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('view_profile.html', user=user)

@app.route('/theme', methods=['POST'])
@login_required
def change_theme():
    theme = request.json.get('theme')
    if theme in ['light', 'dark', 'purple']:
        current_user.theme = theme
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False}), 400

@app.route('/chat/send/<chat_type>/<int:chat_id>', methods=['POST'])
@login_required
def send_message(chat_type, chat_id):
    content = request.form.get('content')
    if not content:
        return jsonify({'success': False, 'error': 'Message content is required'}), 400
    
    if chat_type == 'user':
        message = PrivateMessage(
            sender_id=current_user.id,
            receiver_id=chat_id,
            content=content
        )
    else:  # group chat
        message = GroupMessage(
            sender_id=current_user.id,
            group_id=chat_id,
            content=content
        )
    
    db.session.add(message)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': {
            'content': message.content,
            'time': message.timestamp.strftime('%H:%M'),
            'sent': True
        }
    })

@app.route('/chat/select/<chat_type>/<int:chat_id>')
@login_required
def select_chat(chat_type, chat_id):
    if chat_type == 'user':
        user = User.query.get_or_404(chat_id)
        messages = PrivateMessage.query.filter(
            ((PrivateMessage.sender_id == current_user.id) & (PrivateMessage.receiver_id == chat_id)) |
            ((PrivateMessage.sender_id == chat_id) & (PrivateMessage.receiver_id == current_user.id))
        ).order_by(PrivateMessage.timestamp).all()
        
        # Mark messages as read
        unread_messages = PrivateMessage.query.filter_by(
            sender_id=chat_id,
            receiver_id=current_user.id,
            is_read=False
        ).all()
        for msg in unread_messages:
            msg.is_read = True
        db.session.commit()
        
        return jsonify({
            'name': user.username,
            'avatar': url_for('static', filename=user.avatar_url) if user.avatar_url else None,
            'online': is_user_online(user),
            'messages': [{
                'content': msg.content,
                'time': msg.timestamp.strftime('%H:%M'),
                'sent': msg.sender_id == current_user.id,
                'sender': msg.sender.username,
                'avatar': url_for('static', filename=msg.sender.avatar_url) if msg.sender.avatar_url else None
            } for msg in messages]
        })
    else:
        group = GroupChat.query.get_or_404(chat_id)
        messages = GroupMessage.query.filter_by(group_id=chat_id).order_by(GroupMessage.timestamp).all()
        
        return jsonify({
            'name': group.name,
            'avatar': None,
            'online': True,
            'messages': [{
                'content': msg.content,
                'time': msg.timestamp.strftime('%H:%M'),
                'sent': msg.sender_id == current_user.id,
                'sender': msg.sender.username,
                'avatar': url_for('static', filename=msg.sender.avatar_url) if msg.sender.avatar_url else None
            } for msg in messages]
        })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
