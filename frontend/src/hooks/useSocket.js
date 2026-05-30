/**
 * useSocket — global socket connection state + event subscriptions.
 */
import { useState, useEffect, useCallback } from 'react';
import { toast } from 'react-toastify';
import socket, { onAnomalyAlert, onETLUpdates, onKPIUpdate, offEvent } from '../services/socket';

export default function useSocket(onKPIUpdateCallback) {
  const [connected, setConnected] = useState(socket.connected);

  useEffect(() => {
    const handleConnect    = () => setConnected(true);
    const handleDisconnect = () => setConnected(false);

    socket.on('connect', handleConnect);
    socket.on('disconnect', handleDisconnect);

    // Global event subscriptions
    onAnomalyAlert((data) => {
      toast.error(
        `Anomaly: ${data.content || 'Unknown anomaly detected'}`,
        { icon: false, style: { borderLeft: '3px solid var(--accent-warning)' } }
      );
    });

    onETLUpdates((data) => {
      if (data.status === 'success') {
        toast.success(`ETL complete — ${data.records_processed} records loaded`, { icon: false });
      } else if (data.status === 'failed') {
        toast.error(`ETL failed: ${data.error || 'Unknown error'}`, { icon: false });
      }
    });

    onKPIUpdate((data) => {
      if (onKPIUpdateCallback) onKPIUpdateCallback(data);
    });

    return () => {
      socket.off('connect', handleConnect);
      socket.off('disconnect', handleDisconnect);
      offEvent('anomaly_alert');
      offEvent('etl_complete');
      offEvent('kpi_update');
    };
  }, [onKPIUpdateCallback]);

  return { isConnected: connected };
}
