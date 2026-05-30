/**
 * LiveIndicator — pulsing green dot when WebSocket is connected.
 */
export default function LiveIndicator({ connected }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
      <div style={{ position: 'relative', width: 8, height: 8 }}>
        <div style={{
          width: 8, height: 8, borderRadius: '50%',
          background: connected ? 'var(--accent-success)' : 'var(--text-tertiary)',
        }} />
        {connected && (
          <div style={{
            position: 'absolute', top: 0, left: 0, width: 8, height: 8,
            borderRadius: '50%', background: 'var(--accent-success)',
            animation: 'pulse-ring 2s infinite',
          }} />
        )}
      </div>
      <span style={{ fontSize: 11, fontWeight: 500, color: connected ? 'var(--accent-success)' : 'var(--text-tertiary)' }}>
        {connected ? 'Live' : 'Offline'}
      </span>
    </div>
  );
}
