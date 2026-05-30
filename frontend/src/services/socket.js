/**
 * WebSocket service — socket.io client singleton.
 */
import { io } from 'socket.io-client';

const WS_URL = import.meta.env.VITE_WS_URL || import.meta.env.VITE_API_URL || 'http://localhost:5000';

const socket = io(WS_URL, {
  transports: ['websocket', 'polling'],
  autoConnect: true,
  reconnectionAttempts: 5,
  reconnectionDelay: 1000,
});

export const joinRoom = (roomId, username) =>
  socket.emit('join_room', { room_id: roomId, username });

export const leaveRoom = (roomId, username) =>
  socket.emit('leave_room', { room_id: roomId, username });

export const sendMessage = (roomId, senderName, content) =>
  socket.emit('send_message', { room_id: roomId, sender_name: senderName, content });

export const onNewMessage    = (cb) => socket.on('new_message', cb);
export const onAnomalyAlert  = (cb) => socket.on('anomaly_alert', cb);
export const onETLUpdates    = (cb) => socket.on('etl_complete', cb);
export const onETLStarted    = (cb) => socket.on('etl_started', cb);
export const onKPIUpdate     = (cb) => socket.on('kpi_update', cb);
export const onUserJoined    = (cb) => socket.on('user_joined', cb);
export const onUserLeft      = (cb) => socket.on('user_left', cb);
export const offEvent        = (event) => socket.off(event);
export const isConnected     = () => socket.connected;

export default socket;
