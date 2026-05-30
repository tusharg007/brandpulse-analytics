"""Tests for Celery tasks — mocked Anthropic and SocketIO."""
import os
import pytest
from unittest.mock import patch, MagicMock
from app.models import ChatMessage, ChatRoom


def test_bot_reply_persists_message(app, db):
    """bot_reply task should persist a ChatMessage to the database."""
    with app.app_context():
        room = ChatRoom(name='Bot Test Room', room_type='general')
        db.session.add(room)
        db.session.commit()
        room_id = room.id

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Test bot response")]

        with patch('app.tasks.socketio') as mock_sio:
            with patch('anthropic.Anthropic') as MockClient:
                mock_client_instance = MagicMock()
                mock_client_instance.messages.create.return_value = mock_response
                MockClient.return_value = mock_client_instance

                os.environ['ANTHROPIC_API_KEY'] = 'test-key'

                # Call .run() directly to bypass Celery ContextTask wrapper
                from app.tasks import bot_reply
                bot_reply.run(room_id, "@bot what is our top brand?")

                messages = ChatMessage.query.filter_by(
                    room_id=room_id, sender_type='bot'
                ).all()
                assert len(messages) == 1
                assert messages[0].content == "Test bot response"
                assert messages[0].sender_name == "BrandBot"

                mock_client_instance.messages.create.assert_called_once()
                mock_sio.emit.assert_called()

                os.environ.pop('ANTHROPIC_API_KEY', None)


def test_bot_reply_no_api_key(app, db):
    """bot_reply without API key should return a configuration message."""
    with app.app_context():
        room = ChatRoom(name='No Key Room', room_type='general')
        db.session.add(room)
        db.session.commit()
        room_id = room.id

        os.environ.pop('ANTHROPIC_API_KEY', None)

        with patch('app.tasks.socketio'):
            from app.tasks import bot_reply
            # Call .run() directly to bypass Celery ContextTask wrapper
            bot_reply.run(room_id, "@bot hello")

            msg = ChatMessage.query.filter_by(
                room_id=room_id, sender_type='bot'
            ).first()
            assert msg is not None
            assert "not configured" in msg.content
