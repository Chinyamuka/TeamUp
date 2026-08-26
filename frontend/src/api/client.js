/**
 * API Client for TeamUp Backend
 * Handles all HTTP requests with authentication
 */

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

/**
 * Get the stored access token
 */
const getToken = () => localStorage.getItem('access_token');

/**
 * Set the access token
 */
export const setToken = (token) => localStorage.setItem('access_token', token);

/**
 * Clear the access token
 */
export const clearToken = () => localStorage.removeItem('access_token');

/**
 * Get the stored refresh token
 */
export const getRefreshToken = () => localStorage.getItem('refresh_token');

/**
 * Set the refresh token
 */
export const setRefreshToken = (token) => localStorage.setItem('refresh_token', token);

/**
 * Clear the refresh token
 */
export const clearRefreshToken = () => localStorage.removeItem('refresh_token');

/**
 * API request helper with automatic authentication
 */
export const apiRequest = async (endpoint, options = {}) => {
  const url = `${API_URL}${endpoint}`;
  const token = getToken();

  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const config = {
    ...options,
    headers,
  };

  try {
    const response = await fetch(url, config);
    const data = await response.json();

    if (!response.ok) {
      // Handle token expiration
      if (response.status === 401 && token) {
        // Try to refresh the token
        const refreshed = await refreshAccessToken();
        if (refreshed) {
          // Retry the original request with new token
          return apiRequest(endpoint, options);
        }
      }
      throw new Error(data.error || data.message || 'Request failed');
    }

    return data;
  } catch (error) {
    throw error;
  }
};

/**
 * Refresh the access token using the refresh token
 */
export const refreshAccessToken = async () => {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return false;

  try {
    const response = await fetch(`${API_URL}/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${refreshToken}`,
      },
    });

    const data = await response.json();

    if (response.ok && data.access_token) {
      setToken(data.access_token);
      return true;
    }

    return false;
  } catch (error) {
    return false;
  }
};

// ============================================================
// AUTH API
// ============================================================

export const auth = {
  /**
   * Register a new user
   */
  register: (email, password, fullName) => {
    return apiRequest('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, full_name: fullName }),
    });
  },

  /**
   * Login user
   */
  login: (email, password) => {
    return apiRequest('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  },

  /**
   * Logout user
   */
  logout: () => {
    const refreshToken = getRefreshToken();
    if (refreshToken) {
      return apiRequest('/auth/logout', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${refreshToken}`,
        },
      });
    }
    return Promise.resolve();
  },

  /**
   * Get current user
   */
  me: () => {
    return apiRequest('/auth/me');
  },
};

// ============================================================
// PROJECTS API
// ============================================================

export const projects = {
  /**
   * Get all projects
   */
  list: () => {
    return apiRequest('/projects');
  },

  /**
   * Create a new project
   */
  create: (data) => {
    return apiRequest('/projects', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * Get a single project
   */
  get: (id) => {
    return apiRequest(`/projects/${id}`);
  },

  /**
   * Update a project
   */
  update: (id, data) => {
    return apiRequest(`/projects/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  /**
   * Archive a project
   */
  archive: (id) => {
    return apiRequest(`/projects/${id}`, {
      method: 'DELETE',
    });
  },

  /**
   * Add a member to a project
   */
  addMember: (projectId, email, role = 'member') => {
    return apiRequest(`/projects/${projectId}/members`, {
      method: 'POST',
      body: JSON.stringify({ email, role }),
    });
  },

  /**
   * Remove a member from a project
   */
  removeMember: (projectId, userId) => {
    return apiRequest(`/projects/${projectId}/members/${userId}`, {
      method: 'DELETE',
    });
  },

  /**
   * List project members
   */
  listMembers: (projectId) => {
    return apiRequest(`/projects/${projectId}/members`);
  },
};

// ============================================================
// BOARDS API
// ============================================================

export const boards = {
  /**
   * List boards in a project
   */
  list: (projectId) => {
    return apiRequest(`/boards/project/${projectId}`);
  },

  /**
   * Create a new board
   */
  create: (projectId, data) => {
    return apiRequest(`/boards/project/${projectId}`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * Get a single board
   */
  get: (id) => {
    return apiRequest(`/boards/${id}`);
  },

  /**
   * Update a board
   */
  update: (id, data) => {
    return apiRequest(`/boards/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  /**
   * Archive a board
   */
  archive: (id) => {
    return apiRequest(`/boards/${id}`, {
      method: 'DELETE',
    });
  },

  /**
   * Reorder columns in a board
   */
  reorderColumns: (id, columnOrder) => {
    return apiRequest(`/boards/${id}/reorder`, {
      method: 'POST',
      body: JSON.stringify({ column_order: columnOrder }),
    });
  },
};

// ============================================================
// TASKS API
// ============================================================

export const tasks = {
  /**
   * List tasks in a column
   */
  list: (columnId) => {
    return apiRequest(`/tasks/column/${columnId}/tasks`);
  },

  /**
   * Create a new task
   */
  create: (columnId, data) => {
    return apiRequest(`/tasks/column/${columnId}/tasks`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * Get a single task
   */
  get: (id) => {
    return apiRequest(`/tasks/${id}`);
  },

  /**
   * Update a task
   */
  update: (id, data) => {
    return apiRequest(`/tasks/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  /**
   * Archive a task
   */
  archive: (id) => {
    return apiRequest(`/tasks/${id}`, {
      method: 'DELETE',
    });
  },

  /**
   * Move a task to another column
   */
  move: (id, targetColumnId, position = null) => {
    return apiRequest(`/tasks/${id}/move`, {
      method: 'POST',
      body: JSON.stringify({ target_column_id: targetColumnId, position }),
    });
  },

  /**
   * Reorder tasks in a column
   */
  reorder: (columnId, taskOrder) => {
    return apiRequest(`/tasks/column/${columnId}/reorder`, {
      method: 'POST',
      body: JSON.stringify({ task_order: taskOrder }),
    });
  },

  /**
   * Assign a user to a task
   */
  assign: (taskId, userId) => {
    return apiRequest(`/tasks/${taskId}/assign`, {
      method: 'POST',
      body: JSON.stringify({ user_id: userId }),
    });
  },

  /**
   * Remove a user from a task
   */
  unassign: (taskId, userId) => {
    return apiRequest(`/tasks/${taskId}/assign/${userId}`, {
      method: 'DELETE',
    });
  },

  /**
   * Get task assignees
   */
  getAssignees: (taskId) => {
    return apiRequest(`/tasks/${taskId}/assign`);
  },
};

// ============================================================
// COMMENTS API
// ============================================================

export const comments = {
  /**
   * Add a comment to a task
   */
  add: (taskId, body, parentCommentId = null) => {
    return apiRequest(`/tasks/${taskId}/comments`, {
      method: 'POST',
      body: JSON.stringify({ body, parent_comment_id: parentCommentId }),
    });
  },

  /**
   * List comments on a task
   */
  list: (taskId) => {
    return apiRequest(`/tasks/${taskId}/comments`);
  },

  /**
   * Update a comment
   */
  update: (commentId, body) => {
    return apiRequest(`/comments/${commentId}`, {
      method: 'PUT',
      body: JSON.stringify({ body }),
    });
  },

  /**
   * Delete a comment
   */
  delete: (commentId) => {
    return apiRequest(`/comments/${commentId}`, {
      method: 'DELETE',
    });
  },
};

// ============================================================
// NOTIFICATIONS API
// ============================================================

export const notifications = {
  /**
   * List notifications
   */
  list: (params = {}) => {
    const query = new URLSearchParams(params).toString();
    return apiRequest(`/notifications${query ? `?${query}` : ''}`);
  },

  /**
   * Mark a notification as read
   */
  markRead: (id) => {
    return apiRequest(`/notifications/${id}/read`, {
      method: 'PUT',
    });
  },

  /**
   * Mark all notifications as read
   */
  markAllRead: () => {
    return apiRequest('/notifications/read-all', {
      method: 'PUT',
    });
  },

  /**
   * Get unread count
   */
  getUnreadCount: () => {
    return apiRequest('/notifications/unread-count');
  },

  /**
   * Delete a notification
   */
  delete: (id) => {
    return apiRequest(`/notifications/${id}`, {
      method: 'DELETE',
    });
  },
};

export default {
  auth,
  projects,
  boards,
  tasks,
  comments,
  notifications,
  setToken,
  clearToken,
  getToken,
  setRefreshToken,
  getRefreshToken,
  clearRefreshToken,
};
