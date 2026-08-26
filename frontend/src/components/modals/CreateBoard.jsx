/**
 * Create Board Modal Component
 * 
 * Modal for creating new boards with default columns.
 */

import React, { useState } from 'react';

export const CreateBoard = ({ onClose, onCreate }) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim()) return;

    setLoading(true);
    try {
      await onCreate({
        name: name.trim(),
        description: description.trim(),
        type: 'private',
      });
      onClose();
    } catch (error) {
      console.error('Failed to create board:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/30 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fadeIn">
      <div className="w-full max-w-md bg-white rounded-xl border border-border shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-border flex items-center justify-between">
          <h2 className="text-xl font-bold text-text-primary">Create New Board</h2>
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
              Board Name *
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Product Roadmap"
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
              placeholder="What is this board for?"
              rows={3}
              className="w-full bg-surface-hover border border-border rounded-lg px-4 py-2 focus:border-logic-blue focus:ring-2 focus:ring-logic-blue/20 outline-none transition resize-none"
            />
          </div>

          <div className="bg-surface-hover rounded-lg p-3 text-sm text-text-secondary">
            <p className="font-medium text-text-primary">Default Columns:</p>
            <div className="flex gap-2 mt-1">
              <span className="px-2 py-0.5 bg-white border border-border rounded text-xs">To Do</span>
              <span className="px-2 py-0.5 bg-white border border-border rounded text-xs">In Progress</span>
              <span className="px-2 py-0.5 bg-white border border-border rounded text-xs">Review</span>
              <span className="px-2 py-0.5 bg-white border border-border rounded text-xs">Done</span>
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
              disabled={loading || !name.trim()}
              className="px-6 py-2 bg-logic-blue text-white rounded-lg font-medium hover:bg-logic-blue-dark transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Creating...' : 'Create Board'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
