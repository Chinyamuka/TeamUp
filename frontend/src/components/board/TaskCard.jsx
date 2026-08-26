/**
 * Task Card Component
 * 
 * Displays a single task card in the Kanban column.
 */

import React from 'react';

export const TaskCard = ({ task, onOpen, onDragStart }) => {
  const priorityColors = {
    high: 'border-amber-urgency',
    medium: 'border-logic-blue',
    low: 'border-mint-success',
  };

  return (
    <div
      id={`task-${task.id}`}
      draggable
      onDragStart={(e) => onDragStart(e, task.id)}
      onClick={() => onOpen(task.id)}
      className={`bg-white rounded-lg p-3 cursor-pointer border-l-4 ${priorityColors[task.priority] || 'border-border'} border border-border hover:shadow-md transition-all group`}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-1.5">
        <span className="text-xs font-mono font-semibold text-text-muted bg-surface-hover px-1.5 py-0.5 rounded">
          {task.code || 'TASK'}
        </span>
        {task.priority === 'high' && (
          <span className="text-amber-urgency text-xs font-semibold flex items-center gap-0.5">
            <span className="material-symbols-outlined text-sm">flag</span>
            High
          </span>
        )}
      </div>

      {/* Title */}
      <h4 className="text-sm font-semibold text-text-primary group-hover:text-logic-blue transition line-clamp-2">
        {task.title}
      </h4>

      {/* Footer */}
      <div className="flex items-center justify-between mt-2 pt-2 border-t border-border">
        <div className="flex -space-x-1">
          {task.assignees?.slice(0, 3).map((assignee, idx) => (
            <img
              key={assignee.id || idx}
              src={assignee.avatar || `https://ui-avatars.com/api/?name=${assignee.name}&background=3B4AF5&color=fff`}
              alt={assignee.name}
              className="w-5 h-5 rounded-full border border-white object-cover"
              title={assignee.name}
            />
          ))}
          {task.assignees?.length > 3 && (
            <span className="w-5 h-5 rounded-full border border-white bg-surface-hover text-xs font-mono text-text-secondary flex items-center justify-center">
              +{task.assignees.length - 3}
            </span>
          )}
        </div>

        {task.dueDate && (
          <span className="text-xs text-text-muted flex items-center gap-0.5">
            <span className="material-symbols-outlined text-sm">calendar_today</span>
            {task.dueDate}
          </span>
        )}
      </div>
    </div>
  );
};
