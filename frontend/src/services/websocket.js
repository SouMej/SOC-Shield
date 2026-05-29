/**
 * WebSocket Service — Real-time alert streaming with auto-reconnect.
 */
class WebSocketService {
  constructor() {
    this.ws = null;
    this.listeners = new Map();
    this.reconnectInterval = 3000;
    this.maxReconnectAttempts = 20;
    this.reconnectAttempts = 0;
    this.isConnected = false;
  }

  connect() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.hostname}:8000/api/alerts/stream`;

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this._emit('connection', { connected: true });
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this._emit('message', data);
          if (data.type === 'alert' || data.type === 'ai_alert') {
            this._emit('alert', data.data);
          }
          if (data.type === 'snapshot') {
            this._emit('snapshot', data.data);
          }
        } catch (e) {
          console.error('WS parse error:', e);
        }
      };

      this.ws.onclose = () => {
        this.isConnected = false;
        this._emit('connection', { connected: false });
        this._reconnect();
      };

      this.ws.onerror = (err) => {
        console.error('WS error:', err);
        this.isConnected = false;
      };
    } catch (e) {
      console.error('WS connection error:', e);
      this._reconnect();
    }
  }

  _reconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      setTimeout(() => this.connect(), this.reconnectInterval);
    }
  }

  on(event, callback) {
    if (!this.listeners.has(event)) this.listeners.set(event, []);
    this.listeners.get(event).push(callback);
  }

  off(event, callback) {
    if (!this.listeners.has(event)) return;
    const cbs = this.listeners.get(event).filter(cb => cb !== callback);
    this.listeners.set(event, cbs);
  }

  _emit(event, data) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach(cb => cb(data));
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  sendPing() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send('ping');
    }
  }
}

export const wsService = new WebSocketService();
