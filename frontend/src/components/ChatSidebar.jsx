/**
 * ChatSidebar — Room list with sections and new room modal.
 */
import { useState, useEffect } from 'react';
import { HiPlus, HiMagnifyingGlass } from 'react-icons/hi2';
import api from '../services/api';

export default function ChatSidebar({ activeRoomId, onSelectRoom }) {
  const [rooms, setRooms] = useState([]);
  const [search, setSearch] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [newRoom, setNewRoom] = useState({ name: '', room_type: 'general', brand_id: '' });

  const fetchRooms = () => {
    api.get('/api/chat/rooms').then(r => setRooms(r.data)).catch(() => {});
  };

  useEffect(() => { fetchRooms(); const id = setInterval(fetchRooms, 10000); return () => clearInterval(id); }, []);

  const generalRooms = rooms.filter(r => r.room_type !== 'brand');
  const brandRooms   = rooms.filter(r => r.room_type === 'brand');
  const filtered     = (list) => list.filter(r => r.name.toLowerCase().includes(search.toLowerCase()));

  const handleCreate = async () => {
    try {
      await api.post('/api/chat/rooms', newRoom);
      setShowModal(false);
      setNewRoom({ name: '', room_type: 'general', brand_id: '' });
      fetchRooms();
    } catch { /* ignore */ }
  };

  const RoomRow = ({ room }) => {
    const isActive = room.id === activeRoomId;
    const lastMsg = room.last_message;
    return (
      <div
        onClick={() => onSelectRoom(room.id)}
        style={{
          padding: '8px 12px', cursor: 'pointer',
          background: isActive ? 'var(--bg-elevated)' : 'transparent',
          borderLeft: isActive ? '2px solid var(--accent-primary)' : '2px solid transparent',
          transition: 'background 200ms',
        }}
        onMouseEnter={(e) => { if (!isActive) e.currentTarget.style.background = 'var(--bg-elevated)'; }}
        onMouseLeave={(e) => { if (!isActive) e.currentTarget.style.background = 'transparent'; }}
      >
        <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)', marginBottom: 2 }}>{room.name}</div>
        {lastMsg && (
          <div style={{
            fontSize: 12, color: 'var(--text-tertiary)',
            overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 220,
          }}>
            {lastMsg.sender_name}: {lastMsg.content}
          </div>
        )}
      </div>
    );
  };

  return (
    <div style={{
      width: 280, minWidth: 280, background: 'var(--bg-surface)',
      borderRight: '1px solid var(--bg-border)', display: 'flex', flexDirection: 'column',
      height: '100%', overflow: 'hidden',
    }}>
      {/* Header */}
      <div style={{ padding: '14px 16px 10px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span className="text-sub">Intelligence Feed</span>
        <button
          onClick={() => setShowModal(true)}
          style={{
            width: 28, height: 28, borderRadius: 6, border: '1px solid var(--bg-border)',
            background: 'transparent', color: 'var(--text-secondary)', cursor: 'pointer',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}
        >
          <HiPlus size={14} />
        </button>
      </div>

      {/* Search */}
      <div style={{ padding: '0 12px 10px', position: 'relative' }}>
        <HiMagnifyingGlass size={13} style={{ position: 'absolute', left: 22, top: 9, color: 'var(--text-tertiary)' }} />
        <input
          className="input"
          placeholder="Search rooms..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ width: '100%', paddingLeft: 30, height: 32, fontSize: 12 }}
        />
      </div>

      {/* Room list */}
      <div style={{ flex: 1, overflowY: 'auto' }}>
        {filtered(generalRooms).length > 0 && (
          <>
            <div className="text-label" style={{ padding: '10px 14px 4px' }}>GENERAL</div>
            {filtered(generalRooms).map(r => <RoomRow key={r.id} room={r} />)}
          </>
        )}
        {filtered(brandRooms).length > 0 && (
          <>
            <div className="text-label" style={{ padding: '14px 14px 4px' }}>BRAND ROOMS</div>
            {filtered(brandRooms).map(r => <RoomRow key={r.id} room={r} />)}
          </>
        )}
      </div>

      {/* New room modal */}
      {showModal && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100,
        }}>
          <div className="card" style={{ width: 340, padding: 24 }}>
            <div className="text-sub" style={{ marginBottom: 16 }}>Create Room</div>
            <input
              className="input"
              placeholder="Room name"
              value={newRoom.name}
              onChange={(e) => setNewRoom(n => ({ ...n, name: e.target.value }))}
              style={{ width: '100%', marginBottom: 12 }}
            />
            <select
              className="select-input"
              value={newRoom.room_type}
              onChange={(e) => setNewRoom(n => ({ ...n, room_type: e.target.value }))}
              style={{ width: '100%', marginBottom: 16 }}
            >
              <option value="general">General</option>
              <option value="alerts">Alerts</option>
              <option value="brand">Brand</option>
            </select>
            <div style={{ display: 'flex', gap: 8 }}>
              <button className="btn btn-primary" onClick={handleCreate} style={{ flex: 1 }}>Create</button>
              <button className="btn btn-ghost" onClick={() => setShowModal(false)} style={{ flex: 1 }}>Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
