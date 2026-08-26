/**
 * Create Task Modal Component
 * 
 * Modal for creating new tasks in a board column.
 */

import React, { useState } from 'react';

export const CreateTask = ({ onClose, onCreate, boardId, defaultColumnId, user }) => {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState('medium');
  const [columnId, setColumnId] = useState(defaultColumnId || 'todo');
  const [assignees, setAssignees] = useState([user]);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title.trim()) return;

    setLoading(true);
    try {
      await onCreate({
        title: title.trim(),
        description: description.trim(),
        priority,
        columnId,
        assignees: assignees.map(a => a.id),
      });
      onClose();
    } catch (error) {
      console.error('Failed to create task:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/30 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fadeIn">
      <div className="w-full max-w-lg bg-white rounded-xl border border-border shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-border flex items-center justify-between">
          <h2 className="text-xl font-bold text-text-primary">Create New Task</h2>
          <button
            onClick={onClose}
            className="p-1.5 hover:bg-surface-hover rounded-lg transition text-text-secondary hover:text-text-primary"
          >
            <span className="material-symbols-outlined">close</span>
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-semibold text-text-primary mb-1">
              Task Title *
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Implement rate limiting"
              required
              className="w-full bg-surface-hover border border-border rounded-lg px-4 py-2 focus:border-logic-blue focus:ring-2 focus:ring-logic-blue/20 outline-none transition"
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-text-primary mb-1">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe the task..."
              rows={3}
              className="w-full bg-surface-hover border border-border rounded-lg px-4 py-2 focus:border-logic-blue focus:ring-2 focus:ring-logic-blue/20 outline-none transition resize-none"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-semibold text-text-primary mb-1">
                Priority
              </label>
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value)}
                className="w-full bg-surface-hover border border-border rounded-lg px-4 py-2 focus:border-logic-blue focus:ring-2 focus:ring-logic-blue/20 outline-none transition"
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-semibold text-text-primary mb-1">
                Column
              </label>
              <select
                value={columnId}
                onChange={(e) => setColumnId(e.target.value)}
                className="w-full bg-surface-hover border border-border rounded-lg px-4 py-2 focus:border-logic-blue focus:ring-2 focus:ring-logic-blue/20 outline-none transition"
              >
                <option value="todo">To Do</option>
                <option value="in_progress">In Progress</option>
                <option value="review">Review</option>
                <option value="done">Done</option>
              </select>
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-2 pt-4 border-t border-border">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-lg text-text-secondary hover:bg-surface-hover transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || !title.trim()}
              className="px-6 py-2 bg-logic-blue text-white rounded-lg font-medium hover:bg-logic-blue-dark transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Creating...' : 'Create Task'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
