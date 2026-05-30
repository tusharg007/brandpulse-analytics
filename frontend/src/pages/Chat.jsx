/**
 * Chat — Intelligence Feed page with sidebar + chat window.
 */
import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import ChatSidebar from '../components/ChatSidebar';
import ChatWindow from '../components/ChatWindow';
import { HiChatBubbleLeftRight } from 'react-icons/hi2';

export default function Chat() {
  const { roomId } = useParams();
  const [activeRoomId, setActiveRoomId] = useState(roomId ? parseInt(roomId) : null);
  const [username, setUsername] = useState(() => localStorage.getItem('bp_username') || '');
  const [showNameModal, setShowNameModal] = useState(false);
  const [nameInput, setNameInput] = useState('');

  useEffect(() => {
    if (!username) setShowNameModal(true);
  }, [username]);

  useEffect(() => {
    if (roomId) setActiveRoomId(parseInt(roomId));
  }, [roomId]);

  const handleSetName = () => {
    if (nameInput.trim()) {
      localStorage.setItem('bp_username', nameInput.trim());
      setUsername(nameInput.trim());
      setShowNameModal(false);
    }
  };

  return (
    <div style={{ display: 'flex', height: 'calc(100vh - 56px)', overflow: 'hidden' }}>
      {/* Sidebar */}
      <ChatSidebar activeRoomId={activeRoomId} onSelectRoom={setActiveRoomId} />

      {/* Main area */}
      {activeRoomId ? (
        <ChatWindow roomId={activeRoomId} username={username} />
      ) : (
        <div style={{
          flex: 1, display: 'flex', flexDirection: 'column',
          alignItems: 'center', justifyContent: 'center', gap: 12,
        }}>
          <HiChatBubbleLeftRight size={40} style={{ color: 'var(--text-tertiary)' }} />
          <div style={{ fontSize: 18, fontWeight: 600, color: 'var(--text-secondary)' }}>Select a room</div>
          <div style={{ fontSize: 13, color: 'var(--text-tertiary)', maxWidth: 280, textAlign: 'center' }}>
            Choose a brand room or open General to start chatting with your team and BrandBot.
          </div>
        </div>
      )}

      {/* Username modal */}
      {showNameModal && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100,
        }}>
          <div className="card" style={{ width: 340, padding: 24 }}>
            <div className="text-sub" style={{ marginBottom: 16 }}>Enter your display name</div>
            <input
              className="input"
              placeholder="e.g. Arjun"
              value={nameInput}
              onChange={(e) => setNameInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSetName()}
              style={{ width: '100%', marginBottom: 16 }}
              autoFocus
            />
            <button className="btn btn-primary" onClick={handleSetName} style={{ width: '100%' }}>
              Continue
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
