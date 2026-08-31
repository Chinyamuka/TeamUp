/**
 * Comments Component
 * 
 * Handles adding and displaying comments on tasks.
 */

import React, { useState, useEffect } from 'react';
import { comments as commentsApi } from '../../api/client';

export const Comments = ({ taskId, currentUser, onCommentAdded }) => {
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState('');
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  // Load comments on mount
  useEffect(() => {
    if (taskId) {
      loadComments();
    }
  }, [taskId]);

  const loadComments = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await commentsApi.list(taskId);
      setComments(data.comments || []);
    } catch (err) {
      setError('Failed to load comments');
      console.error('Error loading comments:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!newComment.trim()) return;

    setSubmitting(true);
    setError(null);
    
    try {
      const data = await commentsApi.add(taskId, newComment.trim());
      if (data.comment) {
        setComments([data.comment, ...comments]);
        setNewComment('');
        if (onCommentAdded) {
          onCommentAdded(data.comment);
        }
      }
    } catch (err) {
      setError(err.message || 'Failed to add comment');
      console.error('Error adding comment:', err);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <div className="text-center py-4 text-text-secondary">Loading comments...</div>;
  }

  return (
    <div className="space-y-4">
      {/* Error Message */}
      {error && (
        <div className="bg-error-light border border-error text-on-error-container px-4 py-2 rounded-lg text-sm">
          {error}
        </div>
      )}

      {/* Add Comment Form */}
      <form onSubmit={handleSubmit} className="flex gap-3 items-start">
        <img
          src={currentUser?.avatar || `https://ui-avatars.com/api/?name=${currentUser?.full_name || 'User'}&background=3B4AF5&color=fff`}
          alt={currentUser?.full_name || 'User'}
          className="w-8 h-8 rounded-full object-cover"
        />
        <div className="flex-1">
          <textarea
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
            placeholder="Write a comment..."
            className="w-full border border-border rounded-lg p-2.5 text-sm placeholder-text-muted focus:border-logic-blue focus:ring-2 focus:ring-logic-blue/20 outline-none transition bg-white text-text-primary min-h-[60px] resize-y"
            disabled={submitting}
          />
          <div className="flex justify-end mt-2">
            <button
              type="submit"
              disabled={submitting || !newComment.trim()}
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
      <div className="space-y-3 max-h-[300px] overflow-y-auto">
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
  );
};
