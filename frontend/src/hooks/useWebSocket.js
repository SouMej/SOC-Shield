/**
 * useWebSocket Hook — React hook for real-time WebSocket alerts.
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import { wsService } from '../services/websocket';

export function useWebSocket() {
  const [isConnected, setIsConnected] = useState(false);
  const [alerts, setAlerts] = useState([]);
  const [latestAlert, setLatestAlert] = useState(null);
  const alertsRef = useRef([]);
  const pendingAlertsRef = useRef([]);
  const frameRef = useRef(null);

  useEffect(() => {
    const onConnection = ({ connected }) => setIsConnected(connected);

    const onAlert = (alert) => {
      pendingAlertsRef.current.push(alert);
      
      // Batch updates to avoid freezing the UI on high throughput
      if (!frameRef.current) {
        frameRef.current = requestAnimationFrame(() => {
          const pending = [...pendingAlertsRef.current];
          pendingAlertsRef.current = [];
          frameRef.current = null;

          setAlerts(prev => {
            const newAlerts = [...pending.reverse(), ...prev].slice(0, 100);
            alertsRef.current = newAlerts;
            return newAlerts;
          });
          if (pending.length > 0) {
            setLatestAlert(pending[0]);
          }
        });
      }
    };

    const onSnapshot = (data) => {
      alertsRef.current = Array.isArray(data) ? data : [];
      setAlerts(alertsRef.current);
    };

    wsService.on('connection', onConnection);
    wsService.on('alert', onAlert);
    wsService.on('snapshot', onSnapshot);
    wsService.connect();

    // Heartbeat
    const heartbeat = setInterval(() => wsService.sendPing(), 30000);

    return () => {
      wsService.off('connection', onConnection);
      wsService.off('alert', onAlert);
      wsService.off('snapshot', onSnapshot);
      clearInterval(heartbeat);
      if (frameRef.current) cancelAnimationFrame(frameRef.current);
      wsService.disconnect();
    };
  }, []);

  const clearAlerts = useCallback(() => {
    alertsRef.current = [];
    setAlerts([]);
  }, []);

  return { isConnected, alerts, latestAlert, clearAlerts };
}
