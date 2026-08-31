/**
 * WebSocket Service for Real-time Updates
 * 
 * Manages Socket.IO connection and event handling.
 */

import { io } from 'socket.io-client';

class SocketService {
  constructor() {
    this.socket = null;
    this.connected = false;
    this.listeners = {};
  }

  /**
   * Connect to WebSocket server
   */
  connect(token) {
    if (this.socket && this.connected) {
      console.log('WebSocket already connected');
      return;
    }

    this.socket = io('http://localhost:5000', {
      transports: ['websocket', 'polling'],
      auth: { token },
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
    });

    this.socket.on('connect', () => {
      console.log('✅ WebSocket connected');
      this.connected = true;
      this.emit('connected', { status: 'connected' });
    });

    this.socket.on('disconnect', () => {
      console.log('🔌 WebSocket disconnected');
      this.connected = false;
    });

    this.socket.on('connect_error', (error) => {
      console.error('❌ WebSocket connection error:', error);
    });

    // Setup default event handlers
    this.setupDefaultHandlers();
  }

  /**
   * Setup default event handlers
   */
  setupDefaultHandlers() {
    // Presence updates
    this.on('presence_update', (data) => {
      console.log('👤 Presence update:', data);
    });

    // Task events
    this.on('task_created', (data) => {
      console.log('📝 New task created:', data);
      this.trigger('task_created', data);
    });

    this.on('task_updated', (data) => {
      console.log('✏️ Task updated:', data);
      this.trigger('task_updated', data);
    });

    this.on('task_moved', (data) => {
      console.log('🔀 Task moved:', data);
      this.trigger('task_moved', data);
    });

    this.on('task_deleted', (data) => {
      console.log('🗑️ Task deleted:', data);
      this.trigger('task_deleted', data);
    });
  }

  /**
   * Join a board room
   */
  joinBoard(boardId) {
    if (!this.connected) {
      console.warn('WebSocket not connected');
      return;
    }
    const token = localStorage.getItem('access_token');
    this.emit('join_board', { token, board_id: boardId });
  }

  /**
   * Leave a board room
   */
  leaveBoard(boardId) {
    if (!this.connected) return;
    this.emit('leave_board', { board_id: boardId });
  }

  /**
   * Emit an event
   */
  emit(event, data) {
    if (!this.socket) return;
    this.socket.emit(event, data);
  }

  /**
   * Listen to an event
   */
  on(event, callback) {
    if (!this.socket) return;
    this.socket.on(event, callback);
  }

  /**
   * Remove a listener
   */
  off(event, callback) {
    if (!this.socket) return;
    this.socket.off(event, callback);
  }

  /**
   * Register a custom listener
   */
  addListener(event, callback) {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event].push(callback);
  }

  /**
   * Trigger all listeners for an event
   */
  trigger(event, data) {
    if (this.listeners[event]) {
      this.listeners[event].forEach(callback => callback(data));
    }
  }

  /**
   * Disconnect WebSocket
   */
  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
      this.connected = false;
    }
  }

  /**
   * Check if connected
   */
  isConnected() {
    return this.connected;
  }
}

// Singleton instance
export const socketService = new SocketService();
