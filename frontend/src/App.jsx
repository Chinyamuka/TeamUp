/**
 * TeamUp - Main Application Component
 */

import React, { useState, useEffect } from 'react';
import { auth, projects as projectsApi, boards as boardsApi, tasks as tasksApi, notifications as notificationsApi } from './api/client';
import { SideNav } from './components/layout/SideNav';
import { TopBar } from './components/layout/TopBar';
import { Login } from './components/auth/Login';
import { Dashboard } from './components/dashboard/Dashboard';
import { BoardView } from './components/board/BoardView.jsx';
import { MyTasks } from './components/MyTasks';
import { Notifications } from './components/Notifications';
import { TaskDetail } from './components/modals/TaskDetail.jsx';
import { CreateTask } from './components/modals/CreateTask.jsx';
import { CreateBoard } from './components/modals/CreateBoard.jsx';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [currentView, setCurrentView] = useState('dashboard');
  const [projects, setProjects] = useState([]);
  const [boards, setBoards] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [selectedBoardId, setSelectedBoardId] = useState(null);
  const [selectedTaskId, setSelectedTaskId] = useState(null);
  const [showCreateTask, setShowCreateTask] = useState(false);
  const [showCreateBoard, setShowCreateBoard] = useState(false);
  const [loading, setLoading] = useState(true);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);

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
      fetchProjects();
      fetchBoards();
      fetchNotifications();
    }
  }, [isAuthenticated, currentUser]);

  useEffect(() => {
    if (selectedBoardId && isAuthenticated) {
      fetchTasks(selectedBoardId);
    }
  }, [selectedBoardId, isAuthenticated]);

  const fetchCurrentUser = async () => {
    try {
      const data = await auth.me();
      if (data.user) {
        setCurrentUser(data.user);
        setIsAuthenticated(true);
      }
    } catch (error) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    } finally {
      setLoading(false);
    }
  };

  const fetchProjects = async () => {
    try {
      const data = await projectsApi.list();
      setProjects(data.projects || []);
    } catch (error) {
      console.error('Failed to fetch projects:', error);
    }
  };

  const fetchBoards = async () => {
    try {
      if (projects.length > 0) {
        const data = await boardsApi.list(projects[0].id);
        setBoards(data.boards || []);
        if (data.boards && data.boards.length > 0 && !selectedBoardId) {
          setSelectedBoardId(data.boards[0].id);
        }
      }
    } catch (error) {
      console.error('Failed to fetch boards:', error);
    }
  };

  const fetchTasks = async (boardId) => {
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
        setTasks(allTasks);
      }
    } catch (error) {
      console.error('Failed to fetch tasks:', error);
    }
  };

  const fetchNotifications = async () => {
    try {
      const data = await notificationsApi.list();
      setNotifications(data.notifications || []);
      setUnreadCount(data.unread_count || 0);
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
    }
  };

  const handleLogin = (user, tokens) => {
    setCurrentUser(user);
    setIsAuthenticated(true);
  };

  const handleLogout = async () => {
    try {
      await auth.logout();
    } catch (error) {}
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setIsAuthenticated(false);
    setCurrentUser(null);
    setCurrentView('auth');
  };

  const handleCreateBoard = async (boardData) => {
    try {
      if (projects.length > 0) {
        const data = await boardsApi.create(projects[0].id, boardData);
        if (data.board) {
          setBoards([...boards, data.board]);
          setSelectedBoardId(data.board.id);
          setCurrentView('boards');
        }
      }
    } catch (error) {
      console.error('Failed to create board:', error);
    }
  };

  const handleCreateTask = async (taskData) => {
    try {
      const data = await tasksApi.create(taskData.columnId, taskData);
      if (data.task) {
        const newTask = {
          ...data.task,
          boardId: selectedBoardId,
          columnId: taskData.columnId,
        };
        setTasks([...tasks, newTask]);
      }
    } catch (error) {
      console.error('Failed to create task:', error);
    }
  };

  const handleMoveTask = async (taskId, targetColumnId) => {
    try {
      await tasksApi.move(taskId, targetColumnId);
      const updatedTasks = tasks.map(task => {
        if (task.id === taskId) {
          return { ...task, columnId: targetColumnId };
        }
        return task;
      });
      setTasks(updatedTasks);
    } catch (error) {
      console.error('Failed to move task:', error);
    }
  };

  const handleUpdateTask = async (taskId, data) => {
    try {
      const response = await tasksApi.update(taskId, data);
      if (response.task) {
        const updatedTasks = tasks.map(task => {
          if (task.id === taskId) {
            return { ...task, ...response.task };
          }
          return task;
        });
        setTasks(updatedTasks);
      }
    } catch (error) {
      console.error('Failed to update task:', error);
    }
  };

  const handleDeleteTask = async (taskId) => {
    try {
      await tasksApi.archive(taskId);
      setTasks(tasks.filter(task => task.id !== taskId));
      setSelectedTaskId(null);
    } catch (error) {
      console.error('Failed to delete task:', error);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-logic-blue border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-text-secondary">Loading TeamUp...</p>
        </div>
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
      <SideNav
        currentView={currentView}
        onNavigate={setCurrentView}
        onCreateBoard={() => setShowCreateBoard(true)}
        unreadCount={unreadCount}
        user={currentUser}
        onLogout={handleLogout}
      />

      <div className="flex-1 flex flex-col h-full ml-60 overflow-hidden">
        <TopBar
          currentView={currentView}
          onNavigate={setCurrentView}
          user={currentUser}
          unreadCount={unreadCount}
          onNotificationClick={() => setCurrentView('notifications')}
        />

        <div className="flex-1 overflow-hidden">
          {currentView === 'dashboard' && (
            <Dashboard
              projects={projects}
              boards={boards}
              onSelectBoard={(boardId) => {
                setSelectedBoardId(boardId);
                setCurrentView('boards');
              }}
              onCreateProject={() => setShowCreateBoard(true)}
            />
          )}

          {currentView === 'boards' && activeBoard && (
            <BoardView
              board={activeBoard}
              tasks={tasks}
              onOpenTask={(taskId) => setSelectedTaskId(taskId)}
              onAddTask={(columnId) => {
                setShowCreateTask(true);
                window._createTaskColumn = columnId;
              }}
              onMoveTask={handleMoveTask}
            />
          )}

          {currentView === 'my-tasks' && (
            <MyTasks
              tasks={tasks}
              currentUser={currentUser}
              onOpenTask={(taskId) => setSelectedTaskId(taskId)}
            />
          )}

          {currentView === 'notifications' && (
            <Notifications onOpenTask={(taskId) => setSelectedTaskId(taskId)} />
          )}

          {currentView === 'team' && (
            <div className="p-6">
              <h1 className="text-2xl font-bold text-text-primary mb-4">Team</h1>
              <p className="text-text-secondary">Team members will appear here</p>
            </div>
          )}

          {currentView === 'activity' && (
            <div className="p-6">
              <h1 className="text-2xl font-bold text-text-primary mb-4">Activity</h1>
              <p className="text-text-secondary">Recent activity will appear here</p>
            </div>
          )}

          {currentView === 'reports' && (
            <div className="p-6">
              <h1 className="text-2xl font-bold text-text-primary mb-4">Reports</h1>
              <p className="text-text-secondary">Reports and analytics will appear here</p>
            </div>
          )}

          {currentView === 'settings' && (
            <div className="p-6">
              <h1 className="text-2xl font-bold text-text-primary mb-4">Settings</h1>
              <p className="text-text-secondary">Settings will appear here</p>
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

      {selectedTaskId && activeTask && (
        <TaskDetail
          task={activeTask}
          onClose={() => setSelectedTaskId(null)}
          onUpdate={handleUpdateTask}
          onDelete={handleDeleteTask}
          user={currentUser}
        />
      )}
    </div>
  );
}

export default App;
