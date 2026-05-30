"""Flask-SocketIO event handlers for real-time communication."""
from datetime import datetime
from flask_socketio import join_room, leave_room
from app.extensions import socketio, db
from app.models import ChatMessage


@socketio.on('connect')
def handle_connect():
    """Log client connection."""
    from flask import request
    print(f"Client connected: {request.sid}")


@socketio.on('disconnect')
def handle_disconnect():
    """Log client disconnection."""
    from flask import request
    print(f"Client disconnected: {request.sid}")


@socketio.on('join_room')
def handle_join_room(data):
    """Join a chat room and announce arrival."""
    room_id = data.get('room_id')
    username = data.get('username', 'Anonymous')
    room_key = f"room_{room_id}"

    join_room(room_key)

    # Persist system message
    msg = ChatMessage(
        room_id=room_id,
        sender_name='System',
        sender_type='system',
        content=f"{username} joined the room",
        message_type='text',
        timestamp=datetime.utcnow(),
    )
    db.session.add(msg)
    db.session.commit()

    socketio.emit('user_joined', {
        'username': username,
        'timestamp': datetime.utcnow().isoformat(),
    }, to=room_key)


@socketio.on('leave_room')
def handle_leave_room(data):
    """Leave a chat room."""
    room_id = data.get('room_id')
    username = data.get('username', 'Anonymous')
    room_key = f"room_{room_id}"

    leave_room(room_key)

    socketio.emit('user_left', {
        'username': username,
        'timestamp': datetime.utcnow().isoformat(),
    }, to=room_key)


@socketio.on('send_message')
def handle_send_message(data):
    """Receive and broadcast a user message. Trigger bot if @bot prefix."""
    room_id = data.get('room_id')
    sender_name = data.get('sender_name', 'Anonymous')
    content = data.get('content', '')

    msg = ChatMessage(
        room_id=room_id,
        sender_name=sender_name,
        sender_type='user',
        content=content,
        message_type='text',
        timestamp=datetime.utcnow(),
    )
    db.session.add(msg)
    db.session.commit()

    socketio.emit('new_message', msg.to_dict(), to=f"room_{room_id}")

    # Trigger BrandBot if message starts with @bot
    if content.strip().lower().startswith('@bot'):
        try:
            from app.tasks import bot_reply
            bot_reply.delay(room_id, content)
        except Exception as e:
            print(f"Failed to queue bot reply: {e}")
