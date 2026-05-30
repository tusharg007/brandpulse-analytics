/**
 * ETLPanel — Compact ETL status widget with expandable logs.
 */
import { useState, useEffect } from 'react';
import { triggerETL, getETLLogs } from '../services/api';
import { HiPlay, HiChevronDown, HiChevronUp } from 'react-icons/hi2';

const STATUS_STYLES = {
  idle:    'pill pill-gray',
  queued:  'pill pill-indigo',
  running: 'pill pill-amber',
  success: 'pill pill-emerald',
  failed:  'pill pill-red',
};

export default function ETLPanel() {
  const [status, setStatus] = useState('idle');
  const [logs, setLogs] = useState([]);
  const [expanded, setExpanded] = useState(false);
  const [running, setRunning] = useState(false);

  const fetchLogs = () => {
    getETLLogs().then(r => {
      setLogs(r.data || []);
      if (r.data?.length > 0) setStatus(r.data[0].status);
    }).catch(() => {});
  };

  useEffect(() => { fetchLogs(); }, []);

  const handleTrigger = async () => {
    setRunning(true);
    setStatus('queued');
    try {
      await triggerETL();
      // Poll for completion
      setTimeout(() => {
        fetchLogs();
        setRunning(false);
      }, 3000);
    } catch {
      setStatus('failed');
      setRunning(false);
    }
  };

  const lastLog = logs[0];

  return (
    <div className="card" style={{ padding: 16 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
        <span className={STATUS_STYLES[status] || 'pill pill-gray'}>
          {running && <span style={{ display: 'inline-block', width: 10, height: 10, border: '2px solid currentColor', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 0.6s linear infinite' }} />}
          {status === 'success' && lastLog ? `Success · ${lastLog.records_processed} records` : status.charAt(0).toUpperCase() + status.slice(1)}
        </span>

        {lastLog && (
          <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>
            Last: {new Date(lastLog.run_timestamp).toLocaleString()}
          </span>
        )}

        <div style={{ marginLeft: 'auto', display: 'flex', gap: 8, alignItems: 'center' }}>
          <button
            className="btn"
            onClick={() => setExpanded(!expanded)}
            style={{ padding: '4px 8px', background: 'transparent', color: 'var(--text-secondary)', fontSize: 12 }}
          >
            {expanded ? <HiChevronUp size={14} /> : <HiChevronDown size={14} />}
            Logs
          </button>
          <button className="btn btn-primary" onClick={handleTrigger} disabled={running} style={{ padding: '6px 14px', fontSize: 12 }}>
            <HiPlay size={13} /> Run Pipeline
          </button>
        </div>
      </div>

      {/* Expandable logs table */}
      {expanded && (
        <div style={{ marginTop: 12, overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12, fontFamily: 'monospace' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--bg-border)' }}>
                {['Timestamp', 'Status', 'Records', 'Anomalies', 'Duration'].map(h => (
                  <th key={h} style={{ padding: '6px 10px', textAlign: 'left', color: 'var(--text-tertiary)', fontWeight: 500, fontSize: 11 }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {logs.slice(0, 5).map(log => (
                <tr key={log.id} style={{ borderBottom: '1px solid var(--bg-border)' }}>
                  <td style={{ padding: '6px 10px', color: 'var(--text-secondary)' }}>{new Date(log.run_timestamp).toLocaleString()}</td>
                  <td style={{ padding: '6px 10px' }}><span className={STATUS_STYLES[log.status] || 'pill pill-gray'}>{log.status}</span></td>
                  <td style={{ padding: '6px 10px' }}>{log.records_processed}</td>
                  <td style={{ padding: '6px 10px' }}>{log.anomalies_detected ?? '—'}</td>
                  <td style={{ padding: '6px 10px' }}>{log.duration_seconds ? `${log.duration_seconds}s` : '—'}</td>
                </tr>
              ))}
              {logs.length === 0 && (
                <tr><td colSpan={5} style={{ padding: '12px 10px', color: 'var(--text-tertiary)', textAlign: 'center' }}>No ETL runs yet</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
