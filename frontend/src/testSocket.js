/**
 * Test WebSocket Connection
 */

import { socketService } from './services/socket';

const token = localStorage.getItem('access_token');
if (token) {
  socketService.connect(token);
  console.log('✅ WebSocket test started');
  
  // Test joining a board
  setTimeout(() => {
    socketService.joinBoard(3);
  }, 2000);
} else {
  console.log('❌ No token found. Please login first.');
}
