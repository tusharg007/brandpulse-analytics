"""Chat room and message REST endpoints."""
from flask import Blueprint, request, jsonify
from sqlalchemy import func
from app.extensions import db, socketio
from app.models import ChatRoom, ChatMessage, Brand

chat_bp = Blueprint('chat', __name__)


@chat_bp.route('/api/chat/rooms', methods=['GET'])
def get_rooms():
    """List all chat rooms with last message and message count."""
    rooms = ChatRoom.query.order_by(ChatRoom.created_at).all()
    result = []
    for room in rooms:
        room_dict = room.to_dict()
        last_msg = (
            ChatMessage.query
            .filter_by(room_id=room.id)
            .order_by(ChatMessage.timestamp.desc())
            .first()
        )
        room_dict['last_message'] = last_msg.to_dict() if last_msg else None
        room_dict['message_count'] = ChatMessage.query.filter_by(room_id=room.id).count()
        result.append(room_dict)
    return jsonify(result)


@chat_bp.route('/api/chat/rooms/<int:room_id>/messages', methods=['GET'])
def get_messages(room_id):
    """Get messages for a room with cursor pagination."""
    limit = request.args.get('limit', 50, type=int)
    before_id = request.args.get('before_id', type=int)

    query = ChatMessage.query.filter_by(room_id=room_id)
    if before_id:
        query = query.filter(ChatMessage.id < before_id)
    messages = query.order_by(ChatMessage.timestamp.asc()).limit(limit).all()
    return jsonify([m.to_dict() for m in messages])


@chat_bp.route('/api/chat/rooms', methods=['POST'])
def create_room():
    """Create a new chat room."""
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({"error": "Room name is required"}), 400

    if ChatRoom.query.filter_by(name=data['name']).first():
        return jsonify({"error": "Room name already exists"}), 409

    room = ChatRoom(
        name=data['name'],
        brand_id=data.get('brand_id'),
        room_type=data.get('room_type', 'general'),
    )
    db.session.add(room)
    db.session.flush()

    # Add welcome message
    if data.get('brand_id'):
        brand = db.session.get(Brand, data['brand_id'])
        welcome = f"Room created for {brand.name}. BrandBot is ready -- type @bot to ask questions."
    else:
        welcome = f"Welcome to {data['name']}. BrandBot is ready -- type @bot to ask questions."

    msg = ChatMessage(
        room_id=room.id, sender_name='System',
        sender_type='system', content=welcome, message_type='text',
    )
    db.session.add(msg)
    db.session.commit()

    socketio.emit('room_created', room.to_dict(), namespace='/', to='general')
    return jsonify(room.to_dict()), 201
