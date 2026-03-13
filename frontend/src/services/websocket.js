import { io } from 'socket.io-client';

const WS_URL = process.env.REACT_APP_WS_URL || 'http://localhost:5000';

class WebSocketService {
  constructor() {
    this.socket = null;
    this.listeners = new Map();
  }

  connect() {
    if (this.socket?.connected) {
      console.log('WebSocket already connected');
      return;
    }

    // Disconnect existing socket if any
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }

    console.log(`🔌 Connecting to WebSocket at ${WS_URL}...`);
    console.log(`   Using Socket.IO client version: ${io.version || 'unknown'}`);
    
    this.socket = io(WS_URL, {
      transports: ['polling', 'websocket'],  // Try polling first, then upgrade to websocket
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: Infinity,
      reconnectionDelayMax: 5000,
      timeout: 20000,
      forceNew: true,  // Force a new connection
      autoConnect: true,
      withCredentials: false,
    });

    this.socket.on('connect', () => {
      console.log('✅ WebSocket connected successfully!');
      console.log(`   Socket ID: ${this.socket.id}`);
      this.emit('connected', true);
    });

    this.socket.on('connect_error', (error) => {
      console.error('❌ WebSocket connection error:', error);
      console.error('   Error type:', error.type);
      console.error('   Error message:', error.message);
      if (error.description) {
        console.error('   Error description:', error.description);
      }
      this.emit('error', error);
      this.emit('connected', false);
    });

    this.socket.on('disconnect', (reason) => {
      console.log('⚠️ WebSocket disconnected:', reason);
      this.emit('connected', false);
    });

    this.socket.on('error', (error) => {
      console.error('❌ WebSocket error:', error);
      this.emit('error', error);
    });

    // Listen for the 'connected' event from the server
    this.socket.on('connected', (data) => {
      console.log('📡 Server confirmed connection:', data);
      this.emit('connected', true);
    });

    // Log connection attempts
    this.socket.on('reconnect_attempt', (attemptNumber) => {
      console.log(`🔄 Reconnection attempt #${attemptNumber}`);
    });

    this.socket.on('reconnect', (attemptNumber) => {
      console.log(`✅ Reconnected after ${attemptNumber} attempts`);
      this.emit('connected', true);
    });

    this.socket.on('reconnect_error', (error) => {
      console.error('❌ Reconnection error:', error);
    });

    this.socket.on('reconnect_failed', () => {
      console.error('❌ Reconnection failed after all attempts');
    });

    // Listen for data updates
    this.socket.on('raw_player_added', (data) => {
      this.emit('raw_player_added', data);
    });

    this.socket.on('qualified_lead_updated', (data) => {
      this.emit('qualified_lead_updated', data);
    });

    this.socket.on('identity_match_added', (data) => {
      this.emit('identity_match_added', data);
    });

    this.socket.on('stats_updated', (data) => {
      this.emit('stats_updated', data);
    });
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
    this.listeners.clear();
  }

  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
  }

  off(event, callback) {
    if (this.listeners.has(event)) {
      const callbacks = this.listeners.get(event);
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    }
  }

  emit(event, data) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach((callback) => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Error in listener for ${event}:`, error);
        }
      });
    }
  }

  isConnected() {
    return this.socket?.connected || false;
  }
}

export default new WebSocketService();
