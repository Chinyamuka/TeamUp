/**
 * Data Service with Auto-Fetch and Caching
 */

import { projects as projectsApi, boards as boardsApi, tasks as tasksApi, notifications as notificationsApi } from '../api/client';
import { socketService } from './socket';

class DataService {
  constructor() {
    this.cache = {
      projects: null,
      boards: {},
      tasks: {},
      notifications: null,
    };
    this.pollingInterval = null;
    this.listeners = {};
    this.isPolling = false;
  }

  init(userId, token) {
    this.userId = userId;
    this.token = token;
    socketService.connect(token);
    this.setupWebSocketListeners();
    this.startPolling();
  }

  setupWebSocketListeners() {
    socketService.addListener('task_created', (data) => {
      this.invalidateCache('tasks');
      this.trigger('task_created', data);
    });

    socketService.addListener('task_updated', (data) => {
      this.invalidateCache('tasks');
      this.trigger('task_updated', data);
    });

    socketService.addListener('task_moved', (data) => {
      this.invalidateCache('tasks');
      this.trigger('task_moved', data);
    });

    socketService.addListener('task_deleted', (data) => {
      this.invalidateCache('tasks');
      this.trigger('task_deleted', data);
    });

    socketService.addListener('presence_update', (data) => {
      this.trigger('presence_update', data);
    });
  }

  startPolling(interval = 30000) {
    if (this.isPolling) return;
    this.isPolling = true;
    this.fetchAll();
    this.pollingInterval = setInterval(() => {
      this.fetchAll();
    }, interval);
  }

  stopPolling() {
    this.isPolling = false;
    if (this.pollingInterval) {
      clearInterval(this.pollingInterval);
      this.pollingInterval = null;
    }
    socketService.disconnect();
  }

  async fetchAll() {
    try {
      await Promise.all([
        this.fetchProjects(),
        this.fetchNotifications(),
      ]);
    } catch (error) {
      console.error('Error fetching data:', error);
    }
  }

  async fetchProjects() {
    try {
      const data = await projectsApi.list();
      this.cache.projects = data.projects || [];
      this.trigger('projects_updated', this.cache.projects);
      return this.cache.projects;
    } catch (error) {
      console.error('Error fetching projects:', error);
      return this.cache.projects || [];
    }
  }

  async fetchBoards(projectId) {
    try {
      const data = await boardsApi.list(projectId);
      this.cache.boards[projectId] = data.boards || [];
      this.trigger('boards_updated', { projectId, boards: this.cache.boards[projectId] });
      return this.cache.boards[projectId];
    } catch (error) {
      console.error('Error fetching boards:', error);
      return this.cache.boards[projectId] || [];
    }
  }

  async fetchTasks(boardId) {
    try {
      const boardData = await boardsApi.get(boardId);
      const board = boardData.board;
      
      if (board && board.columns) {
        let allTasks = [];
        for (const column of board.columns) {
          const taskData = await tasksApi.list(column.id);
          allTasks = [...allTasks, ...(taskData.tasks || []).map(t => ({
            ...t,
            columnId: column.id,
            columnName: column.name,
            boardId: board.id,
            boardName: board.name,
          }))];
        }
        this.cache.tasks[boardId] = allTasks;
        this.trigger('tasks_updated', { boardId, tasks: allTasks });
        return allTasks;
      }
      return [];
    } catch (error) {
      console.error('Error fetching tasks:', error);
      return this.cache.tasks[boardId] || [];
    }
  }

  async fetchNotifications() {
    try {
      const data = await notificationsApi.list();
      this.cache.notifications = data.notifications || [];
      this.trigger('notifications_updated', this.cache.notifications);
      return this.cache.notifications;
    } catch (error) {
      console.error('Error fetching notifications:', error);
      return this.cache.notifications || [];
    }
  }

  getProjects() {
    return this.cache.projects || [];
  }

  getBoards(projectId) {
    return this.cache.boards[projectId] || [];
  }

  getTasks(boardId) {
    return this.cache.tasks[boardId] || [];
  }

  getNotifications() {
    return this.cache.notifications || [];
  }

  invalidateCache(type) {
    if (type === 'projects') {
      this.cache.projects = null;
    } else if (type === 'boards') {
      this.cache.boards = {};
    } else if (type === 'tasks') {
      this.cache.tasks = {};
    } else if (type === 'notifications') {
      this.cache.notifications = null;
    }
  }

  on(event, callback) {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event].push(callback);
  }

  trigger(event, data) {
    if (this.listeners[event]) {
      this.listeners[event].forEach(callback => callback(data));
    }
  }

  off(event, callback) {
    if (this.listeners[event]) {
      this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
    }
  }
}

export const dataService = new DataService();
