/**
 * Dashboard Component
 * 
 * Displays projects overview, progress bars, and quick stats.
 */

import React, { useState } from 'react';

export const Dashboard = ({ projects, boards, onSelectBoard, onCreateProject }) => {
  const [filter, setFilter] = useState('all');

  const getStatusColor = (progress) => {
    if (progress >= 80) return 'bg-mint-success';
    if (progress >= 40) return 'bg-logic-blue';
    return 'bg-amber-urgency';
  };

  const getIconColor = (progress) => {
    if (progress >= 80) return 'text-mint-success';
    if (progress >= 40) return 'text-logic-blue';
    return 'text-amber-urgency';
  };

  const filteredProjects = filter === 'all' 
    ? projects 
    : projects.filter(p => p.category?.toLowerCase() === filter);

  // Stats
  const totalProjects = projects.length;
  const completedProjects = projects.filter(p => p.progress === 100).length;
  const avgProgress = totalProjects > 0 
    ? Math.round(projects.reduce((sum, p) => sum + p.progress, 0) / totalProjects) 
    : 0;

  return (
    <main className="flex-1 overflow-y-auto p-6 bg-background select-none">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <div>
            <h2 className="text-3xl font-bold text-text-primary">All Projects</h2>
            <p className="text-text-secondary mt-1">Overview of active initiatives and progress</p>
          </div>
          <button
            onClick={onCreateProject}
            className="bg-logic-blue text-white px-4 py-2 rounded-lg font-medium hover:bg-logic-blue-dark transition flex items-center gap-2"
          >
            <span className="material-symbols-outlined text-lg">add</span>
            New Project
          </button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-white border border-border rounded-xl p-5 shadow-sm">
            <p className="text-sm text-text-secondary">Total Projects</p>
            <p className="text-3xl font-bold text-text-primary">{totalProjects}</p>
          </div>
          <div className="bg-white border border-border rounded-xl p-5 shadow-sm">
            <p className="text-sm text-text-secondary">Completed</p>
            <p className="text-3xl font-bold text-mint-success">{completedProjects}</p>
          </div>
          <div className="bg-white border border-border rounded-xl p-5 shadow-sm">
            <p className="text-sm text-text-secondary">Average Progress</p>
            <p className="text-3xl font-bold text-logic-blue">{avgProgress}%</p>
          </div>
        </div>

        {/* Filter Tabs */}
        <div className="flex gap-2 mb-6">
          {['all', 'infra', 'design', 'backend', 'frontend'].map(cat => (
            <button
              key={cat}
              onClick={() => setFilter(cat)}
              className={`px-3 py-1.5 rounded-full text-sm font-medium capitalize transition ${
                filter === cat
                  ? 'bg-terminal-indigo text-white'
                  : 'bg-white border border-border text-text-secondary hover:bg-surface-hover'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* Project Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredProjects.map((project) => (
            <div
              key={project.id}
              onClick={() => {
                const board = boards.find(b => b.id === project.boardId);
                if (board) onSelectBoard(board.id);
              }}
              className="bg-white border border-border rounded-xl p-5 hover:border-logic-blue hover:shadow-md transition-all cursor-pointer group"
            >
              <div className={`h-1 w-full rounded-full ${getStatusColor(project.progress)} mb-4`} />

              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-surface-hover rounded-lg border border-border">
                    <span className={`material-symbols-outlined ${getIconColor(project.progress)}`}>
                      {project.icon || 'folder'}
                    </span>
                  </div>
                  <div>
                    <h3 className="font-semibold text-text-primary group-hover:text-logic-blue transition">
                      {project.title}
                    </h3>
                    <span className="text-xs font-mono text-text-muted">{project.code}</span>
                  </div>
                </div>
                <span className="text-sm font-bold text-text-primary">{project.progress}%</span>
              </div>

              <div className="w-full bg-surface-hover rounded-full h-2 mb-3">
                <div
                  className={`h-2 rounded-full ${getStatusColor(project.progress)} transition-all`}
                  style={{ width: `${project.progress}%` }}
                />
              </div>

              <div className="flex justify-between items-center text-xs text-text-secondary">
                <span>{project.category || 'General'}</span>
                <span className="flex items-center gap-1">
                  <span className="material-symbols-outlined text-sm">calendar_today</span>
                  {project.dueDate || 'No due date'}
                </span>
              </div>
            </div>
          ))}

          {/* Create New Project Card */}
          <div
            onClick={onCreateProject}
            className="border-2 border-dashed border-border hover:border-logic-blue rounded-xl p-6 flex flex-col items-center justify-center min-h-[180px] cursor-pointer group transition"
          >
            <div className="w-12 h-12 rounded-full bg-surface-hover group-hover:bg-logic-blue/10 flex items-center justify-center mb-3 transition">
              <span className="material-symbols-outlined text-2xl text-text-muted group-hover:text-logic-blue">
                add
              </span>
            </div>
            <p className="font-semibold text-text-primary group-hover:text-logic-blue transition">
              Create New Project
            </p>
            <p className="text-sm text-text-secondary">Spin up a new sprint or kanban board</p>
          </div>
        </div>
      </div>
    </main>
  );
};
