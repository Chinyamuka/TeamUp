/**
 * Column Component
 * 
 * A single column in the Kanban board containing task cards.
 */

import React from 'react';
import { TaskCard } from './TaskCard';

export const Column = ({
  column,
  tasks,
  onOpenTask,
  onAddTask,
  onDragStart,
  onDragOver,
  onDrop,
}) => {
  return (
    <div
      className="w-80 min-w-[280px] max-w-[320px] flex flex-col max-h-full bg-white border border-border rounded-lg shadow-sm"
      onDragOver={onDragOver}
      onDrop={(e) => onDrop(e, column.id)}
    >
      {/* Column Header */}
      <div className="p-3 border-b border-border flex items-center justify-between bg-surface-hover rounded-t-lg">
        <h3 className="font-semibold text-text-primary flex items-center gap-2">
          <span>{column.title}</span>
          <span className="px-2 py-0.5 rounded-full bg-surface-hover text-xs font-mono text-text-secondary">
            {tasks.length}
          </span>
        </h3>
        <button
          onClick={() => onAddTask(column.id)}
          className="text-text-secondary hover:text-logic-blue p-1 rounded hover:bg-logic-blue/10 transition"
        >
          <span className="material-symbols-outlined text-lg">add</span>
        </button>
      </div>

      {/* Tasks Container */}
      <div className="p-2 flex-1 overflow-y-auto space-y-2 min-h-[120px] max-h-[calc(100vh-220px)]">
        {tasks.map((task) => (
          <TaskCard
            key={task.id}
            task={task}
            onOpen={onOpenTask}
            onDragStart={onDragStart}
          />
        ))}

        {tasks.length === 0 && (
          <div
            onClick={() => onAddTask(column.id)}
            className="h-20 border-2 border-dashed border-border rounded-lg flex flex-col items-center justify-center text-text-muted hover:border-logic-blue hover:text-logic-blue cursor-pointer transition"
          >
            <span className="material-symbols-outlined text-lg">add</span>
            <span className="text-xs font-medium">Add task to {column.title}</span>
          </div>
        )}
      </div>
    </div>
  );
};
