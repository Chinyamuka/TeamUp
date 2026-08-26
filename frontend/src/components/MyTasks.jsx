/**
 * My Tasks View Component
 * 
 * Displays tasks assigned to the current user.
 */

import React, { useState } from 'react';

export const MyTasks = ({ tasks, currentUser, onOpenTask }) => {
  const [filter, setFilter] = useState('all');

  const myTasks = tasks.filter(t => 
    t.assignees?.some(a => a.id === currentUser.id)
  );

  const filteredTasks = filter === 'all' 
    ? myTasks 
    : myTasks.filter(t => t.columnId === filter);

  const statusColors = {
    todo: 'bg-amber-urgency',
    in_progress: 'bg-logic-blue',
    review: 'bg-terminal-indigo',
    done: 'bg-mint-success',
  };

  return (
    <main className="flex-1 overflow-y-auto p-6 bg-background select-none">
      <div className="max-w-4xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h2 className="text-3xl font-bold text-text-primary">My Tasks</h2>
            <p className="text-text-secondary mt-1">Tasks assigned to you</p>
          </div>
          <span className="text-sm font-medium text-text-secondary">
            {myTasks.length} tasks
          </span>
        </div>

        {/* Filter Tabs */}
        <div className="flex gap-2 mb-6">
          {['all', 'todo', 'in_progress', 'review', 'done'].map((status) => (
            <button
              key={status}
              onClick={() => setFilter(status)}
              className={`px-3 py-1.5 rounded-full text-sm font-medium capitalize transition ${
                filter === status
                  ? 'bg-terminal-indigo text-white'
                  : 'bg-white border border-border text-text-secondary hover:bg-surface-hover'
              }`}
            >
              {status === 'all' ? 'All' : status.replace('_', ' ')}
            </button>
          ))}
        </div>

        {/* Task List */}
        <div className="space-y-3">
          {filteredTasks.map((task) => (
            <div
              key={task.id}
              onClick={() => onOpenTask(task.id)}
              className="bg-white border border-border rounded-lg p-4 hover:border-logic-blue hover:shadow-md transition-all cursor-pointer"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`w-2 h-2 rounded-full ${statusColors[task.columnId] || 'bg-logic-blue'}`} />
                    <span className="text-xs font-mono font-semibold text-text-muted">
                      {task.code || 'TASK'}
                    </span>
                    {task.priority === 'high' && (
                      <span className="text-amber-urgency text-xs font-semibold flex items-center gap-0.5">
                        <span className="material-symbols-outlined text-sm">flag</span>
                        High
                      </span>
                    )}
                  </div>
                  <h3 className="font-semibold text-text-primary">{task.title}</h3>
                  <p className="text-sm text-text-secondary line-clamp-1">{task.description}</p>
                </div>
                <div className="flex items-center gap-3 ml-4">
                  <span className="text-xs text-text-muted capitalize">
                    {task.columnId?.replace('_', ' ') || 'To Do'}
                  </span>
                  {task.dueDate && (
                    <span className="text-xs text-text-muted flex items-center gap-0.5">
                      <span className="material-symbols-outlined text-sm">calendar_today</span>
                      {task.dueDate}
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}

          {filteredTasks.length === 0 && (
            <div className="text-center py-12 bg-white border border-border rounded-lg">
              <span className="material-symbols-outlined text-4xl text-text-muted">check_circle</span>
              <p className="text-text-secondary mt-2">No tasks in this view</p>
            </div>
          )}
        </div>
      </div>
    </main>
  );
};
