/**
 * Admin Dashboard Component
 * 
 * Professional dashboard for Admin users with analytics and management tools.
 */

import React, { useState, useEffect } from 'react';
import { RoleBadge } from '../common/RoleBadge';
import { PermissionGuard } from '../common/PermissionGuard';

export const AdminDashboard = ({ 
  projects, 
  boards, 
  tasks,
  userRole, 
  currentUser,
  onSelectBoard,
  onCreateProject,
  onInviteMember
}) => {
  const [stats, setStats] = useState({
    totalProjects: 0,
    totalBoards: 0,
    totalTasks: 0,
    completedTasks: 0,
    inProgressTasks: 0,
    todoTasks: 0,
  });

  useEffect(() => {
    // Calculate statistics
    const totalProjects = projects.length;
    const totalBoards = boards.length;
    const allTasks = tasks || [];
    const totalTasks = allTasks.length;
    const completedTasks = allTasks.filter(t => t.columnId === 'done' || t.isDone).length;
    const inProgressTasks = allTasks.filter(t => t.columnId === 'in_progress').length;
    const todoTasks = allTasks.filter(t => t.columnId === 'todo').length;

    setStats({
      totalProjects,
      totalBoards,
      totalTasks,
      completedTasks,
      inProgressTasks,
      todoTasks,
    });
  }, [projects, boards, tasks]);

  // Get time-based greeting
  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good Morning';
    if (hour < 17) return 'Good Afternoon';
    return 'Good Evening';
  };

  return (
    <div className="flex-1 overflow-y-auto p-6 bg-background select-none">
      <div className="max-w-7xl mx-auto">
        {/* Header Section */}
        <div className="mb-8">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-3xl font-bold text-text-primary">
                  {getGreeting()}, {currentUser?.full_name || 'Admin'} 👋
                </h1>
                <RoleBadge role="admin" size="lg" />
              </div>
              <p className="text-text-secondary mt-1">
                You have administrative access to manage projects, members, and workspace settings.
              </p>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={onCreateProject}
                className="bg-logic-blue text-white px-4 py-2 rounded-lg font-medium hover:bg-logic-blue-dark transition flex items-center gap-2 shadow-sm"
              >
                <span className="material-symbols-outlined text-lg">add</span>
                New Project
              </button>
              <button
                onClick={onInviteMember}
                className="bg-white border border-logic-blue text-logic-blue px-4 py-2 rounded-lg font-medium hover:bg-logic-blue/5 transition flex items-center gap-2"
              >
                <span className="material-symbols-outlined text-lg">person_add</span>
                Invite Member
              </button>
            </div>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
          <div className="bg-white border border-border rounded-xl p-4 shadow-sm">
            <p className="text-sm text-text-secondary">Projects</p>
            <p className="text-2xl font-bold text-text-primary">{stats.totalProjects}</p>
          </div>
          <div className="bg-white border border-border rounded-xl p-4 shadow-sm">
            <p className="text-sm text-text-secondary">Boards</p>
            <p className="text-2xl font-bold text-logic-blue">{stats.totalBoards}</p>
          </div>
          <div className="bg-white border border-border rounded-xl p-4 shadow-sm">
            <p className="text-sm text-text-secondary">Total Tasks</p>
            <p className="text-2xl font-bold text-text-primary">{stats.totalTasks}</p>
          </div>
          <div className="bg-white border border-border rounded-xl p-4 shadow-sm">
            <p className="text-sm text-text-secondary">Todo</p>
            <p className="text-2xl font-bold text-amber-urgency">{stats.todoTasks}</p>
          </div>
          <div className="bg-white border border-border rounded-xl p-4 shadow-sm">
            <p className="text-sm text-text-secondary">In Progress</p>
            <p className="text-2xl font-bold text-logic-blue">{stats.inProgressTasks}</p>
          </div>
          <div className="bg-white border border-border rounded-xl p-4 shadow-sm">
            <p className="text-sm text-text-secondary">Completed</p>
            <p className="text-2xl font-bold text-mint-success">{stats.completedTasks}</p>
          </div>
        </div>

        {/* Two Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Projects List */}
          <div className="lg:col-span-2 bg-white border border-border rounded-xl p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-bold text-text-primary">Projects</h2>
              <button onClick={onCreateProject} className="text-sm text-logic-blue hover:underline">
                View All
              </button>
            </div>
            <div className="space-y-3">
              {projects.map((project) => (
                <div
                  key={project.id}
                  onClick={() => {
                    const board = boards.find(b => b.id === project.boardId);
                    if (board) onSelectBoard(board.id);
                  }}
                  className="flex items-center justify-between p-3 border border-border rounded-lg hover:border-logic-blue hover:shadow-sm transition-all cursor-pointer"
                >
                  <div>
                    <p className="font-medium text-text-primary">{project.name}</p>
                    <p className="text-sm text-text-secondary">{project.description || 'No description'}</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-sm text-text-secondary">{project.board_count || 0} boards</span>
                    <span className="text-sm text-text-secondary">{project.member_count || 1} members</span>
                    <span className="material-symbols-outlined text-text-muted">arrow_forward</span>
                  </div>
                </div>
              ))}
              {projects.length === 0 && (
                <p className="text-center text-text-secondary py-4">No projects yet</p>
              )}
            </div>
          </div>

          {/* Quick Actions */}
          <div className="bg-white border border-border rounded-xl p-6">
            <h2 className="text-lg font-bold text-text-primary mb-4">Quick Actions</h2>
            <div className="space-y-2">
              <button className="w-full flex items-center gap-3 p-3 border border-border rounded-lg hover:border-logic-blue hover:bg-logic-blue/5 transition text-left">
                <span className="material-symbols-outlined text-logic-blue">add_task</span>
                <span className="text-sm font-medium text-text-primary">Create New Task</span>
              </button>
              <button className="w-full flex items-center gap-3 p-3 border border-border rounded-lg hover:border-logic-blue hover:bg-logic-blue/5 transition text-left">
                <span className="material-symbols-outlined text-logic-blue">group_add</span>
                <span className="text-sm font-medium text-text-primary">Invite Team Member</span>
              </button>
              <button className="w-full flex items-center gap-3 p-3 border border-border rounded-lg hover:border-logic-blue hover:bg-logic-blue/5 transition text-left">
                <span className="material-symbols-outlined text-logic-blue">settings</span>
                <span className="text-sm font-medium text-text-primary">Manage Workspace</span>
              </button>
              <button className="w-full flex items-center gap-3 p-3 border border-border rounded-lg hover:border-logic-blue hover:bg-logic-blue/5 transition text-left">
                <span className="material-symbols-outlined text-logic-blue">analytics</span>
                <span className="text-sm font-medium text-text-primary">View Reports</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
