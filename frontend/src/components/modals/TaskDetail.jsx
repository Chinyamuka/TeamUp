/**
 * Task Detail Modal Component
 * 
 * Displays full task information with comments, activities, and actions.
 */

import React, { useState } from 'react';

export const TaskDetail = ({ task, onClose, onUpdate, onDelete, user }) => {
  const [commentText, setCommentText] = useState('');
  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState(task.title);
  const [editDescription, setEditDescription] = useState(task.description || '');

  const priorityColors = {
    high: 'bg-amber-urgency',
    medium: 'bg-logic-blue',
    low: 'bg-mint-success',
  };

  const handleAddComment = () => {
    if (!commentText.trim()) return;
    const newComment = {
      id: `comment_${Date.now()}`,
      author: user,
      body: commentText.trim(),
      created_at: new Date().toISOString(),
    };
    const updatedComments = [...(task.comments || []), newComment];
    onUpdate(task.id, { comments: updatedComments });
    setCommentText('');
  };

  const handleSaveEdit = () => {
    onUpdate(task.id, {
      title: editTitle,
      description: editDescription,
    });
    setIsEditing(false);
  };

  const handleStatusChange = (newStatus) => {
    onUpdate(task.id, { status: newStatus });
  };

  return (
    <div className="fixed inset-0 bg-black/30 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fadeIn">
      <div className="w-full max-w-4xl max-h-[90vh] bg-white rounded-xl border border-border shadow-2xl flex flex-col overflow-hidden">
        {/* Header */}
        <div className={`h-1 w-full ${priorityColors[task.priority] || 'bg-logic-blue'}`} />

        <div className="flex items-center justify-between px-6 py-4 border-b border-border">
          <div className="flex items-center gap-2 text-sm text-text-secondary">
            <span className="font-mono font-bold text-text-primary">{task.code || 'TASK'}</span>
            <span>•</span>
            <span>{task.boardName || 'No Board'}</span>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 hover:bg-surface-hover rounded-lg transition text-text-secondary hover:text-text-primary"
          >
            <span className="material-symbols-outlined">close</span>
          </button>
        </div>

        {/* Body */}
        <div className="flex flex-1 overflow-hidden">
          {/* Main Content */}
          <div className="flex-1 p-6 overflow-y-auto border-r border-border">
            {isEditing ? (
              <div className="space-y-4">
                <input
                  type="text"
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                  className="w-full text-2xl font-bold bg-surface-hover border border-border rounded-lg px-4 py-2 focus:border-logic-blue focus:ring-2 focus:ring-logic-blue/20 outline-none"
                  placeholder="Task title"
                />
                <textarea
                  value={editDescription}
                  onChange={(e) => setEditDescription(e.target.value)}
                  className="w-full min-h-[100px] bg-surface-hover border border-border rounded-lg px-4 py-2 focus:border-logic-blue focus:ring-2 focus:ring-logic-blue/20 outline-none"
                  placeholder="Task description..."
                />
                <div className="flex gap-2">
                  <button
                    onClick={handleSaveEdit}
                    className="px-4 py-2 bg-logic-blue text-white rounded-lg font-medium hover:bg-logic-blue-dark transition"
                  >
                    Save Changes
                  </button>
                  <button
                    onClick={() => setIsEditing(false)}
                    className="px-4 py-2 bg-surface-hover text-text-secondary rounded-lg font-medium hover:bg-border transition"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <>
                <h2 className="text-2xl font-bold text-text-primary mb-2">{task.title}</h2>
                <p className="text-text-secondary mb-4">{task.description || 'No description provided.'}</p>

                {/* Labels */}
                {task.labels?.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mb-4">
                    {task.labels.map((label, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-0.5 bg-surface-hover text-text-secondary text-xs font-medium rounded-full"
                      >
                        {label}
                      </span>
                    ))}
                  </div>
                )}

                <button
                  onClick={() => setIsEditing(true)}
                  className="text-sm text-logic-blue hover:underline"
                >
                  Edit Task
                </button>

                {/* Comments */}
                <div className="mt-6">
                  <h3 className="font-semibold text-text-primary mb-3">Comments</h3>
                  <div className="space-y-3 max-h-[200px] overflow-y-auto">
                    {(task.comments || []).map((comment) => (
                      <div key={comment.id} className="flex gap-3">
                        <img
                          src={comment.author?.avatar || `https://ui-avatars.com/api/?name=${comment.author?.name || 'User'}&background=3B4AF5&color=fff`}
                          alt={comment.author?.name}
                          className="w-8 h-8 rounded-full object-cover"
                        />
                        <div className="flex-1 bg-surface-hover rounded-lg p-3">
                          <div className="flex justify-between items-center mb-1">
                            <span className="font-medium text-sm text-text-primary">
                              {comment.author?.name || 'Unknown'}
                            </span>
                            <span className="text-xs text-text-muted">
                              {comment.created_at ? new Date(comment.created_at).toLocaleDateString() : ''}
                            </span>
                          </div>
                          <p className="text-sm text-text-secondary">{comment.body}</p>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Add Comment */}
                  <div className="mt-3 flex gap-2">
                    <input
                      type="text"
                      value={commentText}
                      onChange={(e) => setCommentText(e.target.value)}
                      placeholder="Add a comment..."
                      className="flex-1 bg-surface-hover border border-border rounded-lg px-3 py-2 text-sm focus:border-logic-blue focus:ring-2 focus:ring-logic-blue/20 outline-none"
                      onKeyDown={(e) => e.key === 'Enter' && handleAddComment()}
                    />
                    <button
                      onClick={handleAddComment}
                      disabled={!commentText.trim()}
                      className="px-4 py-2 bg-logic-blue text-white rounded-lg font-medium hover:bg-logic-blue-dark transition disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Send
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>

          {/* Sidebar */}
          <div className="w-64 p-6 bg-surface-hover flex flex-col gap-4">
            <div>
              <label className="text-xs font-semibold text-text-secondary uppercase block mb-1">
                Status
              </label>
              <select
                value={task.columnId || 'todo'}
                onChange={(e) => handleStatusChange(e.target.value)}
                className="w-full bg-white border border-border rounded-lg px-3 py-2 text-sm focus:border-logic-blue focus:ring-2 focus:ring-logic-blue/20 outline-none"
              >
                <option value="todo">To Do</option>
                <option value="in_progress">In Progress</option>
                <option value="review">Review</option>
                <option value="done">Done</option>
              </select>
            </div>

            <div>
              <label className="text-xs font-semibold text-text-secondary uppercase block mb-1">
                Priority
              </label>
              <div className="flex gap-1">
                {['low', 'medium', 'high'].map((p) => (
                  <button
                    key={p}
                    onClick={() => onUpdate(task.id, { priority: p })}
                    className={`flex-1 px-2 py-1.5 rounded-lg text-xs font-medium capitalize transition ${
                      task.priority === p
                        ? 'bg-logic-blue text-white'
                        : 'bg-white border border-border text-text-secondary hover:bg-surface-hover'
                    }`}
                  >
                    {p}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold text-text-secondary uppercase block mb-1">
                Assignees
              </label>
              <div className="flex flex-wrap gap-1">
                {(task.assignees || []).map((assignee) => (
                  <span
                    key={assignee.id}
                    className="inline-flex items-center gap-1 px-2 py-0.5 bg-white border border-border rounded-full text-xs"
                  >
                    <img
                      src={assignee.avatar || `https://ui-avatars.com/api/?name=${assignee.name}&background=3B4AF5&color=fff`}
                      alt={assignee.name}
                      className="w-4 h-4 rounded-full object-cover"
                    />
                    {assignee.name}
                  </span>
                ))}
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold text-text-secondary uppercase block mb-1">
                Due Date
              </label>
              <input
                type="date"
                value={task.dueDate || ''}
                onChange={(e) => onUpdate(task.id, { due_date: e.target.value })}
                className="w-full bg-white border border-border rounded-lg px-3 py-2 text-sm focus:border-logic-blue focus:ring-2 focus:ring-logic-blue/20 outline-none"
              />
            </div>

            <div className="border-t border-border pt-4 mt-auto">
              <button
                onClick={() => onDelete(task.id)}
                className="w-full px-4 py-2 bg-error-light text-error rounded-lg font-medium hover:bg-error/10 transition"
              >
                Delete Task
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
