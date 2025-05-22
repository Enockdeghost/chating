from flask_socketio import emit
from flask_login import current_user
from models import db, Message, User, Notification
from datetime import datetime

def handle_typing(data):
    room = data['room']
    emit('typing', {
        'user': current_user.username,
        'typing': data['typing']
    }, room=room)

def handle_read_receipt(data):
    message_id = data['message_id']
    message = Message.query.get(message_id)
    if message:
        message.read_at = datetime.utcnow()
        db.session.commit()
        emit('message_read', {
            'message_id': message_id,
            'reader': current_user.username
        }, room=data['room']) 