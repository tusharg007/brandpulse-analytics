/**
 * ChatWindow — Message display + input bar with WebSocket real-time messaging.
 */
import { useState, useEffect, useRef } from 'react';
import { HiPaperAirplane } from 'react-icons/hi2';
import api from '../services/api';
import { joinRoom, leaveRoom, sendMessage, onNewMessage, onUserJoined, offEvent } from '../services/socket';
import MessageBubble from './MessageBubble';

export default function ChatWindow({ roomId, username }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [roomInfo, setRoomInfo] = useState(null);
  const messagesEndRef = useRef(null);
  const prevRoomRef = useRef(null);

  // Fetch messages and join room
  useEffect(() => {
    if (!roomId) return;

    // Leave previous room
    if (prevRoomRef.current && prevRoomRef.current !== roomId) {
      leaveRoom(prevRoomRef.current, username);
    }
    prevRoomRef.current = roomId;

    // Fetch messages
    api.get(`/api/chat/rooms/${roomId}/messages?limit=100`)
      .then(r => setMessages(r.data))
      .catch(() => setMessages([]));

    // Join room via socket
    joinRoom(roomId, username);

    // Listen for new messages
    const handleNewMsg = (msg) => {
      if (msg.room_id === roomId) {
        setMessages(prev => [...prev, msg]);
      }
    };
    onNewMessage(handleNewMsg);

    return () => {
      offEvent('new_message');
    };
  }, [roomId, username]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = () => {
    if (!input.trim() || !roomId) return;
    sendMessage(roomId, username, input.trim());
    setInput('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Group consecutive messages from same sender
  const groupedMessages = messages.map((msg, i) => ({
    ...msg,
    isFirst: i === 0 || messages[i - 1].sender_name !== msg.sender_name || messages[i - 1].sender_type !== msg.sender_type,
  }));

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Header */}
      <div style={{
        height: 56, minHeight: 56, padding: '0 24px',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        borderBottom: '1px solid var(--bg-border)', background: 'var(--bg-surface)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ fontSize: 15, fontWeight: 600 }}>Room #{roomId}</span>
        </div>
      </div>

      {/* Messages area */}
      <div style={{
        flex: 1, overflowY: 'auto', padding: '16px 24px',
        display: 'flex', flexDirection: 'column', gap: 2,
      }}>
        {messages.length === 0 && (
          <div style={{ textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 13, marginTop: 40 }}>
            No messages yet. Start a conversation!
          </div>
        )}
        {groupedMessages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} isFirst={msg.isFirst} />
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input bar */}
      <div style={{
        height: 64, minHeight: 64, padding: '12px 24px',
        borderTop: '1px solid var(--bg-border)', background: 'var(--bg-surface)',
        display: 'flex', alignItems: 'center', gap: 10,
      }}>
        <input
          className="input"
          placeholder={`Message · Type @bot to ask BrandBot`}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          style={{ flex: 1, height: 40, borderRadius: 8, padding: '10px 14px', fontSize: 14 }}
        />
        <button
          className="btn btn-primary"
          onClick={handleSend}
          disabled={!input.trim()}
          style={{ height: 40, width: 40, padding: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: 8 }}
        >
          <HiPaperAirplane size={16} />
        </button>
      </div>
    </div>
  );
}
