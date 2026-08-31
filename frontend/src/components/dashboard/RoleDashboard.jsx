/**
 * Role-Based Dashboard Component
 */

import React, { useState, useEffect } from 'react';
import { RoleBadge } from '../common/RoleBadge';
import { PermissionGuard } from '../common/PermissionGuard';

export const RoleDashboard = ({ 
  projects, 
  boards, 
  userRole, 
  currentUser,
  onSelectBoard,
  onCreateProject 
}) => {
  const [stats, setStats] = useState({
    totalProjects: 0,
    totalBoards: 0,
    totalTasks: 0,
    completedTasks: 0,
  });

  useEffect(() => {
    const totalProjects = projects.length;
    const totalBoards = boards.length;
    setStats({ totalProjects, totalBoards, totalTasks: 0, completedTasks: 0 });
  }, [projects, boards]);

  const getGreeting = () => {
    const hour = new Date().getHours();
    let timeOfDay = 'Good morning';
    if (hour >= 12 && hour < 17) timeOfDay = 'Good afternoon';
    if (hour >= 17) timeOfDay = 'Good evening';
    return `${timeOfDay}, ${currentUser?.full_name || 'User'}!`;
  };

  const getRoleMessage = () => {
    const messages = {
      owner: 'You have full control over this workspace.',
      admin: 'You can manage projects and members.',
      member: 'You can create and work on tasks.',
      viewer: 'You have read-only access to this workspace.',
    };
    return messages[userRole] || 'Welcome to TeamUp!';
  };

  return (
    <div className="flex-1 overflow-y-auto p-6 bg-background select-none">
      <div className="max-w-7xl mx-auto">
        {/* Welcome Section */}
        <div className="mb-8">
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-3xl font-bold text-text-primary">{getGreeting()}</h1>
              <p className="text-text-secondary mt-1">{getRoleMessage()}</p>
            </div>
            <div className="flex items-center gap-3">
              <RoleBadge role={userRole} size="lg" />
              <span className="text-sm text-text-secondary">{currentUser?.email}</span>
            </div>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white border border-border rounded-xl p-5 shadow-sm">
            <p className="text-sm text-text-secondary">Total Projects</p>
            <p className="text-3xl font-bold text-text-primary">{stats.totalProjects}</p>
          </div>
          <div className="bg-white border border-border rounded-xl p-5 shadow-sm">
            <p className="text-sm text-text-secondary">Active Boards</p>
            <p className="text-3xl font-bold text-logic-blue">{stats.totalBoards}</p>
          </div>
          <div className="bg-white border border-border rounded-xl p-5 shadow-sm">
            <p className="text-sm text-text-secondary">Total Tasks</p>
            <p className="text-3xl font-bold text-mint-success">{stats.totalTasks}</p>
          </div>
          <div className="bg-white border border-border rounded-xl p-5 shadow-sm">
            <p className="text-sm text-text-secondary">Completed</p>
            <p className="text-3xl font-bold text-amber-urgency">{stats.completedTasks}</p>
          </div>
        </div>

        {/* Project Grid */}
        <div className="mb-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-bold text-text-primary">Projects</h2>
            <PermissionGuard userRole={userRole} requiredRole="member">
              <button
                onClick={onCreateProject}
                className="bg-logic-blue text-white px-4 py-2 rounded-lg font-medium hover:bg-logic-blue-dark transition flex items-center gap-2"
              >
                <span className="material-symbols-outlined text-lg">add</span>
                New Project
              </button>
            </PermissionGuard>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {projects.map((project) => (
              <div
                key={project.id}
                onClick={() => {
                  const board = boards.find(b => b.id === project.boardId);
                  if (board) onSelectBoard(board.id);
                }}
                className="bg-white border border-border rounded-xl p-5 hover:border-logic-blue hover:shadow-md transition-all cursor-pointer group"
              >
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h3 className="font-semibold text-text-primary group-hover:text-logic-blue transition">
                      {project.name}
                    </h3>
                    <p className="text-sm text-text-secondary line-clamp-1">
                      {project.description || 'No description'}
                    </p>
                  </div>
                  <RoleBadge role={project.user_role || userRole} size="sm" />
                </div>
                <div className="flex items-center justify-between text-sm text-text-secondary">
                  <span>{project.board_count || 0} boards</span>
                  <span>{project.member_count || 0} members</span>
                </div>
              </div>
            ))}

            {projects.length === 0 && (
              <div className="col-span-full text-center py-12 bg-white border border-border rounded-xl">
                <span className="material-symbols-outlined text-4xl text-text-muted">folder</span>
                <p className="text-text-secondary mt-2">No projects yet</p>
                <PermissionGuard userRole={userRole} requiredRole="member">
                  <button
                    onClick={onCreateProject}
                    className="mt-3 text-logic-blue hover:underline"
                  >
                    Create your first project
                  </button>
                </PermissionGuard>
              </div>
            )}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white border border-border rounded-xl p-5">
            <h3 className="font-semibold text-text-primary mb-3">Recent Activity</h3>
            <div className="space-y-3">
              <p className="text-sm text-text-secondary">No recent activity</p>
            </div>
          </div>
          <div className="bg-white border border-border rounded-xl p-5">
            <h3 className="font-semibold text-text-primary mb-3">Quick Actions</h3>
            <div className="space-y-2">
              <PermissionGuard userRole={userRole} requiredRole="member">
                <button className="w-full text-left px-3 py-2 bg-surface-hover rounded-lg hover:bg-logic-blue/10 transition text-sm">
                  <span className="material-symbols-outlined text-lg mr-2">add_task</span>
                  Create New Task
                </button>
              </PermissionGuard>
              <PermissionGuard userRole={userRole} requiredRole="admin">
                <button className="w-full text-left px-3 py-2 bg-surface-hover rounded-lg hover:bg-logic-blue/10 transition text-sm">
                  <span className="material-symbols-outlined text-lg mr-2">group_add</span>
                  Invite Teammate
                </button>
              </PermissionGuard>
              <button className="w-full text-left px-3 py-2 bg-surface-hover rounded-lg hover:bg-logic-blue/10 transition text-sm">
                <span className="material-symbols-outlined text-lg mr-2">search</span>
                Search Tasks
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
