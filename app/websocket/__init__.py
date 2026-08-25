"""
WebSocket Module

This module handles all WebSocket functionality for real-time updates.
It provides real-time collaboration features as required by SRS Section 7.2.

SRS References:
- Section 7.2: WebSocket Events (Socket.IO)
- Section 5.3: Real-Time Fan-Out Design
- FR-4.1: Real-time broadcast within 500ms
- FR-5.1: Presence indicators
"""

from app.websocket.events import register_socket_handlers

__all__ = ['register_socket_handlers']
