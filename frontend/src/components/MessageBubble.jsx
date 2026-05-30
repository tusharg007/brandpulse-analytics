/**
 * MessageBubble — Renders a single chat message based on sender_type.
 */
import AnomalyBadge from './AnomalyBadge';

export default function MessageBubble({ message, isFirst }) {
  const { sender_name, sender_type, content, message_type, timestamp } = message;
  const time = timestamp ? new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '';

  // System messages — centered italic
  if (sender_type === 'system') {
    return (
      <div style={{
        textAlign: 'center', fontSize: 12, fontStyle: 'italic',
        color: 'var(--text-tertiary)', padding: '8px 0',
      }}>
        {content}
      </div>
    );
  }

  // Anomaly alert message
  if (message_type === 'anomaly_alert') {
    return (
      <div style={{ padding: '6px 0' }}>
        {isFirst && (
          <div style={{ fontSize: 12, color: 'var(--accent-bot)', marginBottom: 4, fontWeight: 500 }}>
            BrandBot
          </div>
        )}
        <AnomalyBadge content={content} timestamp={time} />
      </div>
    );
  }

  // Bot messages
  if (sender_type === 'bot') {
    return (
      <div style={{ padding: '3px 0', maxWidth: '75%' }}>
        {isFirst && (
          <div style={{ fontSize: 12, color: 'var(--accent-bot)', marginBottom: 4, fontWeight: 500 }}>
            BrandBot
          </div>
        )}
        <div style={{
          background: 'var(--bg-elevated)',
          borderLeft: '3px solid var(--accent-bot)',
          borderRadius: '0 8px 8px 8px',
          padding: '10px 14px', fontSize: 14,
          color: 'var(--text-primary)',
        }}>
          {content}
          <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 4 }}>{time}</div>
        </div>
      </div>
    );
  }

  // User messages
  return (
    <div style={{ padding: '3px 0' }}>
      {isFirst && (
        <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 4, fontWeight: 500 }}>
          {sender_name}
        </div>
      )}
      <div style={{ fontSize: 14, color: 'var(--text-primary)', lineHeight: 1.5 }}>
        {content}
        <span style={{ fontSize: 11, color: 'var(--text-tertiary)', marginLeft: 8 }}>{time}</span>
      </div>
    </div>
  );
}
