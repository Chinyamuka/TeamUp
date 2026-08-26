/**
 * Board View Component
 * 
 * Kanban board with columns and draggable tasks.
 */

import React, { useState } from 'react';
import { Column } from './Column.jsx';

export const BoardView = ({ board, tasks, onOpenTask, onAddTask, onMoveTask }) => {
  const [draggedTaskId, setDraggedTaskId] = useState(null);

  const getColumnTasks = (columnId) => {
    return tasks.filter(t => t.columnId === columnId);
  };

  const handleDragStart = (e, taskId) => {
    e.dataTransfer.setData('text/plain', taskId);
    setDraggedTaskId(taskId);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDrop = (e, targetColumnId) => {
    e.preventDefault();
    const taskId = e.dataTransfer.getData('text/plain') || draggedTaskId;
    if (taskId) {
      onMoveTask(taskId, targetColumnId);
    }
    setDraggedTaskId(null);
  };

  if (!board) {
    return (
      <div className="flex-1 flex items-center justify-center p-6">
        <p className="text-text-secondary">Select a board to get started</p>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden bg-background select-none">
      {/* Board Header */}
      <div className="px-6 py-4 border-b border-border bg-white">
        <h1 className="text-2xl font-bold text-text-primary">{board.name}</h1>
        <p className="text-sm text-text-secondary">{board.description || 'No description'}</p>
      </div>

      {/* Columns */}
      <div className="flex-1 overflow-x-auto p-6 flex gap-4 items-start">
        {board.columns?.map((column) => (
          <Column
            key={column.id}
            column={column}
            tasks={getColumnTasks(column.id)}
            onOpenTask={onOpenTask}
            onAddTask={onAddTask}
            onDragStart={handleDragStart}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
          />
        ))}
      </div>
    </div>
  );
};
