/**
 * Task Detail Modal Component with Working Comments
 */

import React, { useState, useEffect } from 'react';
import { tasks as tasksApi, comments as commentsApi } from '../../api/client';

export const TaskDetail = ({ task, onClose, onUpdate, onDelete, user, userRole }) => {
  const [commentText, setCommentText] = useState('');
  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState(task.title);
  const [editDescription, setEditDescription] = useState(task.description || '');
  const [comments, setComments] = useState(task.comments || []);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [isCopied, setIsCopied] = useState(false);

  // Load comments when task changes
  useEffect(() => {
    loadComments();
  }, [task.id]);

  const loadComments = async () => {
    try {
      const data = await commentsApi.list(task.id);
      setComments(data.comments || []);
    } catch (err) {
      console.error('Error loading comments:', err);
    }
  };

  const priorityColors = {
    high: 'bg-amber-urgency',
    medium: 'bg-logic-blue',
    low: 'bg-mint-success',
  };

  const handleAddComment = async (e) => {
    e.preventDefault();
    if (!commentText.trim()) return;

    setSubmitting(true);
    setError(null);
    setSuccess(null);

    try {
      const data = await commentsApi.add(task.id, commentText.trim());
      if (data.comment) {
        setComments([data.comment, ...comments]);
        setCommentText('');
        setSuccess('Comment added successfully!');
        setTimeout(() => setSuccess(null), 3000);
        onUpdate(task.id, { comments: [data.comment, ...comments] });
      }
    } catch (err) {
      setError(err.message || 'Failed to add comment');
      console.error('Error adding comment:', err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleSaveEdit = () => {
    onUpdate(task.id, {
      title: editTitle,
      description: editDescription,
    });
    setIsEditing(false);
  };

  const handleStatusChange = (newStatus) => {
    onUpdate(task.id, { columnId: newStatus });
  };

  const handleCopyLink = () => {
    navigator.clipboard?.writeText(window.location.href);
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 2000);
  };

  const canEdit = userRole === 'owner' || userRole === 'admin' || userRole === 'member';

  return (
    <div className="fixed inset-0 bg-black/30 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fadeIn">
      <div className="w-full max-w-4xl max-h-[90vh] bg-white rounded-xl border border-border shadow-2xl flex flex-col overflow-hidden">
        {/* Priority Strip */}
        <div className={`h-1 w-full ${priorityColors[task.priority] || 'bg-logic-blue'}`} />

        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border">
          <div className="flex items-center gap-3">
            <span className="text-xs font-mono font-bold text-text-muted bg-surface-hover px-2 py-0.5 rounded">
              {task.code || 'TASK'}
            </span>
            <span className="text-xs text-text-secondary">•</span>
            <span className="text-xs text-text-secondary">{task.boardName || 'No Board'}</span>
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

                {canEdit && (
                  <button
                    onClick={() => setIsEditing(true)}
                    className="text-sm text-logic-blue hover:underline"
                  >
                    Edit Task
                  </button>
                )}

                {/* Comments */}
                <div className="mt-6">
                  <h3 className="font-semibold text-text-primary mb-3">Comments</h3>
                  
                  {/* Success/Error Messages */}
                  {success && (
                    <div className="bg-mint-success/10 border border-mint-success text-mint-success px-4 py-2 rounded-lg mb-3 text-sm">
                      {success}
                    </div>
                  )}
                  {error && (
                    <div className="bg-error-light border border-error text-on-error-container px-4 py-2 rounded-lg mb-3 text-sm">
                      {error}
                    </div>
                  )}

                  {/* Add Comment */}
                  <form onSubmit={handleAddComment} className="flex gap-3 items-start mb-4">
                    <img
                      src={user?.avatar || `https://ui-avatars.com/api/?name=${user?.full_name || 'User'}&background=3B4AF5&color=fff`}
                      alt={user?.full_name || 'User'}
                      className="w-8 h-8 rounded-full object-cover"
                    />
                    <div className="flex-1">
                      <textarea
                        value={commentText}
                        onChange={(e) => setCommentText(e.target.value)}
                        placeholder="Write a comment..."
                        className="w-full border border-border rounded-lg p-2.5 text-sm placeholder-text-muted focus:border-logic-blue focus:ring-2 focus:ring-logic-blue/20 outline-none transition bg-white text-text-primary min-h-[60px] resize-y"
                        disabled={submitting}
                      />
                      <div className="flex justify-end mt-2">
                        <button
                          type="submit"
                          disabled={submitting || !commentText.trim()}
                          className="bg-logic-blue text-white font-medium text-sm px-4 py-1.5 rounded-lg hover:bg-logic-blue-dark transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1.5"
                        >
                          {submitting ? (
                            <>
                              <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                              Sending...
                            </>
                          ) : (
                            <>
                              <span className="material-symbols-outlined text-base">send</span>
                              Comment
                            </>
                          )}
                        </button>
                      </div>
                    </div>
                  </form>

                  {/* Comments List */}
                  <div className="space-y-3 max-h-[200px] overflow-y-auto">
                    {comments.length === 0 ? (
                      <p className="text-center text-text-secondary py-4 text-sm">No comments yet</p>
                    ) : (
                      comments.map((comment) => (
                        <div key={comment.id} className="flex gap-3 items-start">
                          <img
                            src={comment.author?.avatar || `https://ui-avatars.com/api/?name=${comment.author?.full_name || 'User'}&background=3B4AF5&color=fff`}
                            alt={comment.author?.full_name || 'User'}
                            className="w-7 h-7 rounded-full object-cover"
                          />
                          <div className="flex-1 bg-surface-hover rounded-lg p-3">
                            <div className="flex justify-between items-center mb-0.5">
                              <span className="text-sm font-semibold text-text-primary">
                                {comment.author?.full_name || 'Unknown'}
                              </span>
                              <span className="text-xs text-text-muted">
                                {comment.created_at ? new Date(comment.created_at).toLocaleDateString() : ''}
                              </span>
                            </div>
                            <p className="text-sm text-text-secondary">{comment.body}</p>
                          </div>
                        </div>
                      ))
                    )}
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
                disabled={!canEdit}
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
                    disabled={!canEdit}
                    className={`flex-1 px-2 py-1.5 rounded-lg text-xs font-medium capitalize transition ${
                      task.priority === p
                        ? 'bg-logic-blue text-white'
                        : 'bg-white border border-border text-text-secondary hover:bg-surface-hover'
                    } ${!canEdit ? 'opacity-50 cursor-not-allowed' : ''}`}
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
                {(!task.assignees || task.assignees.length === 0) && (
                  <span className="text-xs text-text-muted">No assignees</span>
                )}
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
                disabled={!canEdit}
              />
            </div>

            <div className="border-t border-border pt-4 mt-auto space-y-2">
              <button
                onClick={handleCopyLink}
                className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-white border border-border rounded hover:bg-surface-hover transition text-text-primary text-sm font-medium"
              >
                <span className="material-symbols-outlined text-base">
                  {isCopied ? 'check' : 'link'}
                </span>
                <span>{isCopied ? 'Link Copied!' : 'Copy Link'}</span>
              </button>

              {canEdit && (
                <button
                  onClick={() => { onDelete(task.id); onClose(); }}
                  className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-white border border-border rounded hover:bg-error-light hover:text-error hover:border-error/30 transition text-text-secondary text-sm font-medium"
                >
                  <span className="material-symbols-outlined text-base">delete</span>
                  <span>Delete Task</span>
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
