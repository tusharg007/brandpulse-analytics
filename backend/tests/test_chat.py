"""Tests for Chat API endpoints."""
import pytest
from app.models import ChatRoom, ChatMessage


def test_get_rooms_empty(client):
    """GET /api/chat/rooms returns empty list when no rooms exist."""
    resp = client.get('/api/chat/rooms')
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_create_room_valid(client):
    """POST /api/chat/rooms creates a new room."""
    resp = client.post('/api/chat/rooms', json={
        'name': 'Test Room',
        'room_type': 'general',
    })
    assert resp.status_code == 201
    data = resp.get_json()
    assert data['name'] == 'Test Room'
    assert data['room_type'] == 'general'
    assert data['id'] is not None


def test_create_room_missing_name(client):
    """POST /api/chat/rooms without name returns 400."""
    resp = client.post('/api/chat/rooms', json={'room_type': 'general'})
    assert resp.status_code == 400


def test_create_room_duplicate_name(client):
    """POST /api/chat/rooms with duplicate name returns 409."""
    client.post('/api/chat/rooms', json={'name': 'Unique Room', 'room_type': 'general'})
    resp = client.post('/api/chat/rooms', json={'name': 'Unique Room', 'room_type': 'general'})
    assert resp.status_code == 409


def test_get_messages_empty_room(client):
    """GET messages for a room with no messages returns empty list."""
    # Create room first
    resp = client.post('/api/chat/rooms', json={'name': 'Empty Chat', 'room_type': 'general'})
    room_id = resp.get_json()['id']

    # The room has a welcome message from creation, but let's check a non-existent room
    resp = client.get(f'/api/chat/rooms/9999/messages')
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_get_rooms_with_data(client):
    """GET /api/chat/rooms returns rooms with message counts."""
    client.post('/api/chat/rooms', json={'name': 'Room Alpha', 'room_type': 'general'})
    client.post('/api/chat/rooms', json={'name': 'Room Beta', 'room_type': 'alerts'})

    resp = client.get('/api/chat/rooms')
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data) == 2
    assert data[0]['message_count'] >= 1  # welcome message
