/**
 * TeamUp - Main Application Component with Real-time Updates
 */

import React, { useState, useEffect } from 'react';
import { auth, projects as projectsApi, boards as boardsApi, tasks as tasksApi, notifications as notificationsApi } from './api/client';
import { dataService } from './services/dataService';
import { socketService } from './services/socket';
import { SideNav } from './components/layout/SideNav';
import { TopBar } from './components/layout/TopBar';
import { Login } from './components/auth/Login';
import { RoleDashboard } from './components/dashboard/RoleDashboard';
import { AdminDashboard } from './components/dashboard/AdminDashboard';
import { BoardView } from './components/board/BoardView.jsx';
import { MyTasks } from './components/MyTasks';
import { Notifications } from './components/Notifications';
import { Team } from './components/Team';
import { ActivityFeed } from './components/ActivityFeed';
import { TaskDetail } from './components/modals/TaskDetail.jsx';
import { CreateTask } from './components/modals/CreateTask.jsx';
import { CreateBoard } from './components/modals/CreateBoard.jsx';
import { Toast } from './components/common/Toast';
import { LoadingSpinner } from './components/common/LoadingSpinner';
import { SearchBar } from './components/common/SearchBar';

function App() {
  // Authentication State
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [userRole, setUserRole] = useState(null);
  const [loading, setLoading] = useState(true);

  // Navigation State
  const [currentView, setCurrentView] = useState('dashboard');

  // Data State
  const [projects, setProjects] = useState([]);
  const [boards, setBoards] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [filteredTasks, setFilteredTasks] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [activities, setActivities] = useState([]);
  const [selectedBoardId, setSelectedBoardId] = useState(null);
  const [selectedTaskId, setSelectedTaskId] = useState(null);
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  // Modal State
  const [showCreateTask, setShowCreateTask] = useState(false);
  const [showCreateBoard, setShowCreateBoard] = useState(false);
  const [isInviteOpen, setIsInviteOpen] = useState(false);

  // UI State
  const [toast, setToast] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState({ priority: 'all', status: 'all' });

  // ============================================================
  // INITIALIZATION
  // ============================================================

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      fetchCurrentUser();
    } else {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isAuthenticated && currentUser) {
      dataService.init(currentUser.id, localStorage.getItem('access_token'));
      setupDataListeners();
      fetchAllData();
      loadActivities();
    }
  }, [isAuthenticated, currentUser]);

  useEffect(() => {
    if (selectedBoardId && isAuthenticated) {
      socketService.joinBoard(selectedBoardId);
      fetchTasks(selectedBoardId);
    }
  }, [selectedBoardId, isAuthenticated]);

  useEffect(() => {
    // Apply filters and search to tasks
    let result = tasks;
    
    // Search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      result = result.filter(t => 
        t.title.toLowerCase().includes(query) ||
        t.description?.toLowerCase().includes(query) ||
        t.code?.toLowerCase().includes(query)
      );
    }
    
    // Priority filter
    if (filters.priority && filters.priority !== 'all') {
      result = result.filter(t => t.priority === filters.priority);
    }
    
    // Status filter
    if (filters.status && filters.status !== 'all') {
      result = result.filter(t => t.columnId === filters.status);
    }
    
    setFilteredTasks(result);
  }, [tasks, searchQuery, filters]);

  // ============================================================
  // DATA FETCHING
  // ============================================================

  const fetchCurrentUser = async () => {
    try {
      const data = await auth.me();
      if (data.user) {
        setCurrentUser(data.user);
        setIsAuthenticated(true);
        if (data.user.role) {
          setUserRole(data.user.role);
        }
        showToast(`Welcome back, ${data.user.full_name}!`, 'success');
      }
    } catch (error) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    } finally {
      setLoading(false);
    }
  };

  const fetchAllData = async () => {
    await dataService.fetchAll();
  };

  const fetchTasks = async (boardId) => {
    const taskData = await dataService.fetchTasks(boardId);
    setTasks(taskData);
    setFilteredTasks(taskData);
  };

  const loadActivities = async () => {
    // Simulate loading activities
    const mockActivities = [
      { id: 1, user: currentUser?.full_name || 'System', action: 'created task', target: 'API Documentation', timeAgo: 'Just now' },
      { id: 2, user: currentUser?.full_name || 'System', action: 'updated task', target: 'Fix login bug', timeAgo: '5 minutes ago' },
      { id: 3, user: currentUser?.full_name || 'System', action: 'moved task to', target: 'Done', timeAgo: '1 hour ago' },
    ];
    setActivities(mockActivities);
  };

  const setupDataListeners = () => {
    dataService.on('projects_updated', (projectsData) => {
      setProjects(projectsData);
      if (projectsData && projectsData.length > 0 && projectsData[0].user_role) {
        setUserRole(projectsData[0].user_role);
      }
      if (projectsData && projectsData.length > 0) {
        fetchBoardsForProject(projectsData[0].id);
      }
    });

    dataService.on('boards_updated', ({ projectId, boards: boardsData }) => {
      setBoards(boardsData);
      if (boardsData && boardsData.length > 0 && !selectedBoardId) {
        setSelectedBoardId(boardsData[0].id);
      }
    });

    dataService.on('tasks_updated', ({ boardId, tasks: tasksData }) => {
      if (boardId === selectedBoardId) {
        setTasks(tasksData);
        setFilteredTasks(tasksData);
        showToast('Tasks updated in real-time!', 'info');
      }
    });

    dataService.on('task_created', (taskData) => {
      showToast(`New task created: ${taskData.title}`, 'success');
      if (selectedBoardId) {
        fetchTasks(selectedBoardId);
      }
    });

    dataService.on('task_updated', (taskData) => {
      showToast(`Task updated: ${taskData.title}`, 'info');
      if (selectedBoardId) {
        fetchTasks(selectedBoardId);
      }
    });

    dataService.on('task_moved', (taskData) => {
      showToast(`Task moved: ${taskData.title}`, 'info');
      if (selectedBoardId) {
        fetchTasks(selectedBoardId);
      }
    });

    dataService.on('task_deleted', (taskData) => {
      showToast(`Task deleted: ${taskData.title}`, 'warning');
      if (selectedBoardId) {
        fetchTasks(selectedBoardId);
      }
    });

    dataService.on('notifications_updated', (notificationsData) => {
      setNotifications(notificationsData);
      const unread = notificationsData.filter(n => !n.is_read).length;
      setUnreadCount(unread);
      if (unread > 0) {
        showToast(`You have ${unread} new notification${unread > 1 ? 's' : ''}`, 'info');
      }
    });

    dataService.on('presence_update', (presenceData) => {
      console.log('👤 Real-time: Presence update', presenceData);
    });
  };

  const fetchBoardsForProject = async (projectId) => {
    const boardsData = await dataService.fetchBoards(projectId);
    setBoards(boardsData);
    if (boardsData && boardsData.length > 0 && !selectedBoardId) {
      setSelectedBoardId(boardsData[0].id);
    }
  };

  // ============================================================
  // UI HELPERS
  // ============================================================

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  // ============================================================
  // HANDLERS
  // ============================================================

  const handleLogin = (user, tokens) => {
    setCurrentUser(user);
    setIsAuthenticated(true);
    if (user.role) {
      setUserRole(user.role);
    }
    showToast(`Welcome, ${user.full_name}!`, 'success');
  };

  const handleLogout = async () => {
    try {
      await auth.logout();
    } catch (error) {}
    dataService.stopPolling();
    socketService.disconnect();
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setIsAuthenticated(false);
    setCurrentUser(null);
    setUserRole(null);
    setCurrentView('auth');
    showToast('Logged out successfully', 'info');
  };

  const handleCreateBoard = async (boardData) => {
    try {
      if (projects.length > 0) {
        const data = await boardsApi.create(projects[0].id, boardData);
        if (data.board) {
          await fetchAllData();
          setSelectedBoardId(data.board.id);
          setCurrentView('boards');
          showToast(`Board "${data.board.name}" created!`, 'success');
        }
      }
    } catch (error) {
      showToast('Failed to create board', 'error');
      console.error('Failed to create board:', error);
    }
  };

  const handleCreateTask = async (taskData) => {
    try {
      const data = await tasksApi.create(taskData.columnId, taskData);
      if (data.task) {
        if (selectedBoardId) {
          await fetchTasks(selectedBoardId);
        }
        showToast(`Task "${data.task.title}" created!`, 'success');
      }
    } catch (error) {
      showToast('Failed to create task', 'error');
      console.error('Failed to create task:', error);
    }
  };

  const handleMoveTask = async (taskId, targetColumnId) => {
    try {
      await tasksApi.move(taskId, targetColumnId);
      if (selectedBoardId) {
        await fetchTasks(selectedBoardId);
      }
      showToast('Task moved successfully!', 'success');
    } catch (error) {
      showToast('Failed to move task', 'error');
      console.error('Failed to move task:', error);
    }
  };

  const handleUpdateTask = async (taskId, data) => {
    try {
      const response = await tasksApi.update(taskId, data);
      if (response.task) {
        if (selectedBoardId) {
          await fetchTasks(selectedBoardId);
        }
        showToast('Task updated successfully!', 'success');
      }
    } catch (error) {
      showToast('Failed to update task', 'error');
      console.error('Failed to update task:', error);
    }
  };

  const handleDeleteTask = async (taskId) => {
    try {
      await tasksApi.archive(taskId);
      if (selectedBoardId) {
        await fetchTasks(selectedBoardId);
      }
      setSelectedTaskId(null);
      showToast('Task deleted successfully', 'warning');
    } catch (error) {
      showToast('Failed to delete task', 'error');
      console.error('Failed to delete task:', error);
    }
  };

  const handleSearch = (query, filters) => {
    setSearchQuery(query);
    if (filters) {
      setFilters(filters);
    }
  };

  const handleRefreshActivity = () => {
    loadActivities();
    showToast('Activity feed refreshed!', 'info');
  };

  // ============================================================
  // RENDER
  // ============================================================

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <LoadingSpinner size="lg" text="Loading TeamUp..." />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Login onLogin={handleLogin} />;
  }

  const activeBoard = boards.find(b => b.id === selectedBoardId) || null;
  const activeTask = tasks.find(t => t.id === selectedTaskId) || null;

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background">
      {/* Toast Notification */}
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}

      <SideNav
        currentView={currentView}
        onNavigate={setCurrentView}
        onCreateBoard={() => setShowCreateBoard(true)}
        unreadCount={unreadCount}
        user={currentUser}
        onLogout={handleLogout}
        userRole={userRole}
        isOnline={isOnline}
      />

      <div className="flex-1 flex flex-col h-full ml-60 overflow-hidden">
        <TopBar
          currentView={currentView}
          onNavigate={setCurrentView}
          user={currentUser}
          unreadCount={unreadCount}
          onNotificationClick={() => setCurrentView('notifications')}
          userRole={userRole}
          isOnline={isOnline}
        />

        <div className="flex-1 overflow-y-auto p-4">
          {currentView === 'dashboard' && (
            userRole === 'admin' ? (
              <AdminDashboard
                projects={projects}
                boards={boards}
                tasks={tasks}
                userRole={userRole}
                currentUser={currentUser}
                onSelectBoard={(boardId) => {
                  setSelectedBoardId(boardId);
                  setCurrentView('boards');
                }}
                onCreateProject={() => setShowCreateBoard(true)}
                onInviteMember={() => setIsInviteOpen(true)}
              />
            ) : (
              <RoleDashboard
                projects={projects}
                boards={boards}
                userRole={userRole}
                currentUser={currentUser}
                onSelectBoard={(boardId) => {
                  setSelectedBoardId(boardId);
                  setCurrentView('boards');
                }}
                onCreateProject={() => setShowCreateBoard(true)}
              />
            )
          )}

          {currentView === 'boards' && activeBoard && (
            <BoardView
              board={activeBoard}
              tasks={filteredTasks}
              onOpenTask={(taskId) => setSelectedTaskId(taskId)}
              onAddTask={(columnId) => {
                setShowCreateTask(true);
                window._createTaskColumn = columnId;
              }}
              onMoveTask={handleMoveTask}
              userRole={userRole}
              currentUser={currentUser}
            />
          )}

          {currentView === 'my-tasks' && (
            <div className="max-w-6xl mx-auto">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
                <h1 className="text-2xl font-bold text-text-primary">My Tasks</h1>
                <SearchBar
                  onSearch={handleSearch}
                  placeholder="Search my tasks..."
                />
              </div>
              <MyTasks
                tasks={filteredTasks}
                currentUser={currentUser}
                onOpenTask={(taskId) => setSelectedTaskId(taskId)}
                userRole={userRole}
              />
            </div>
          )}

          {currentView === 'notifications' && (
            <Notifications 
              onOpenTask={(taskId) => setSelectedTaskId(taskId)} 
              userRole={userRole}
            />
          )}

          {currentView === 'team' && (
            <Team 
              currentUser={currentUser} 
              onInvite={() => setIsInviteOpen(true)}
              userRole={userRole}
            />
          )}

          {currentView === 'activity' && (
            <div className="max-w-4xl mx-auto">
              <ActivityFeed 
                activities={activities} 
                onRefresh={handleRefreshActivity}
              />
            </div>
          )}

          {currentView === 'reports' && (
            <div className="max-w-6xl mx-auto">
              <h1 className="text-2xl font-bold text-text-primary mb-6">Analytics & Reports</h1>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <div className="bg-white border border-border rounded-xl p-6">
                  <h3 className="font-semibold text-text-primary">Task Completion Rate</h3>
                  <p className="text-3xl font-bold text-mint-success mt-2">
                    {tasks.length > 0 ? Math.round((tasks.filter(t => t.columnId === 'done').length / tasks.length) * 100) : 0}%
                  </p>
                  <p className="text-sm text-text-secondary mt-1">Overall progress</p>
                </div>
                <div className="bg-white border border-border rounded-xl p-6">
                  <h3 className="font-semibold text-text-primary">Active Tasks</h3>
                  <p className="text-3xl font-bold text-logic-blue mt-2">
                    {tasks.filter(t => t.columnId !== 'done').length}
                  </p>
                  <p className="text-sm text-text-secondary mt-1">In progress</p>
                </div>
                <div className="bg-white border border-border rounded-xl p-6">
                  <h3 className="font-semibold text-text-primary">Projects</h3>
                  <p className="text-3xl font-bold text-amber-urgency mt-2">{projects.length}</p>
                  <p className="text-sm text-text-secondary mt-1">Total workspaces</p>
                </div>
              </div>
            </div>
          )}

          {currentView === 'settings' && (
            <div className="max-w-2xl mx-auto">
              <h1 className="text-2xl font-bold text-text-primary mb-6">Settings</h1>
              <div className="bg-white border border-border rounded-xl p-6 space-y-6">
                <div>
                  <h3 className="font-semibold text-text-primary mb-2">Profile</h3>
                  <div className="flex items-center gap-4">
                    <img
                      src={currentUser?.avatar || `https://ui-avatars.com/api/?name=${currentUser?.full_name || 'User'}&background=3B4AF5&color=fff`}
                      alt={currentUser?.full_name}
                      className="w-16 h-16 rounded-full object-cover"
                    />
                    <div>
                      <p className="font-medium text-text-primary">{currentUser?.full_name}</p>
                      <p className="text-sm text-text-secondary">{currentUser?.email}</p>
                      <p className="text-sm text-logic-blue capitalize">{userRole}</p>
                    </div>
                  </div>
                </div>
                <div className="border-t border-border pt-4">
                  <h3 className="font-semibold text-text-primary mb-2">Preferences</h3>
                  <div className="space-y-2">
                    <label className="flex items-center gap-2">
                      <input type="checkbox" defaultChecked className="rounded border-border" />
                      <span className="text-sm text-text-secondary">Email notifications</span>
                    </label>
                    <label className="flex items-center gap-2">
                      <input type="checkbox" defaultChecked className="rounded border-border" />
                      <span className="text-sm text-text-secondary">Real-time updates</span>
                    </label>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {showCreateTask && (
        <CreateTask
          onClose={() => setShowCreateTask(false)}
          onCreate={handleCreateTask}
          boardId={selectedBoardId}
          defaultColumnId={window._createTaskColumn || 'todo'}
          user={currentUser}
        />
      )}

      {showCreateBoard && (
        <CreateBoard
          onClose={() => setShowCreateBoard(false)}
          onCreate={handleCreateBoard}
        />
      )}

      {isInviteOpen && (
        <div className="fixed inset-0 bg-black/30 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fadeIn">
          <div className="w-full max-w-md bg-white rounded-xl border border-border shadow-2xl overflow-hidden">
            <div className="px-6 py-4 border-b border-border flex items-center justify-between">
              <h2 className="text-xl font-bold text-text-primary">Invite Teammate</h2>
              <button
                onClick={() => setIsInviteOpen(false)}
                className="p-1.5 hover:bg-surface-hover rounded-lg transition"
              >
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>
            <div className="p-6">
              <p className="text-text-secondary text-sm mb-4">
                Send an invitation to a colleague to join your workspace.
              </p>
              <input
                type="email"
                placeholder="colleague@company.com"
                className="w-full bg-surface-hover border border-border rounded-lg px-4 py-2 mb-4 focus:border-logic-blue focus:ring-2 focus:ring-logic-blue/20 outline-none"
              />
              <div className="flex justify-end gap-2">
                <button
                  onClick={() => setIsInviteOpen(false)}
                  className="px-4 py-2 rounded-lg text-text-secondary hover:bg-surface-hover transition"
                >
                  Cancel
                </button>
                <button
                  onClick={() => {
                    showToast('Invitation sent successfully!', 'success');
                    setIsInviteOpen(false);
                  }}
                  className="px-4 py-2 bg-logic-blue text-white rounded-lg font-medium hover:bg-logic-blue-dark transition"
                >
                  Send Invite
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {selectedTaskId && activeTask && (
        <TaskDetail
          task={activeTask}
          onClose={() => setSelectedTaskId(null)}
          onUpdate={handleUpdateTask}
          onDelete={handleDeleteTask}
          user={currentUser}
          userRole={userRole}
        />
      )}
    </div>
  );
}

export default App;
