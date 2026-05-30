/**
 * AnomalyBadge — Alert card for anomaly messages in chat.
 */
import { HiExclamationTriangle } from 'react-icons/hi2';

export default function AnomalyBadge({ content, timestamp }) {
  return (
    <div style={{
      border: '1px solid var(--accent-warning)',
      borderRadius: 8, padding: '12px 16px',
      borderLeft: '4px solid var(--accent-warning)',
      background: 'rgba(245,158,11,0.05)',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8 }}>
        <HiExclamationTriangle size={15} style={{ color: 'var(--accent-warning)' }} />
        <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--accent-warning)' }}>Anomaly Detected</span>
      </div>
      <div style={{ fontSize: 13, color: 'var(--text-primary)', lineHeight: 1.5 }}>
        {content}
      </div>
      {timestamp && (
        <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 6 }}>{timestamp}</div>
      )}
    </div>
  );
}
