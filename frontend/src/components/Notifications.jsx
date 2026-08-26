/**
 * Notifications Component
 * 
 * Displays all notifications for the current user with:
 * - Unread/read status
 * - Mark as read functionality
 * - Mark all as read
 * - Click to navigate to related task
 */

import React, { useState, useEffect } from 'react';
import { notifications as notificationsApi } from '../api/client';

export const Notifications = ({ onOpenTask }) => {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [unreadCount, setUnreadCount] = useState(0);

  // Fetch notifications on mount
  useEffect(() => {
    fetchNotifications();
  }, []);

  const fetchNotifications = async () => {
    try {
      setLoading(true);
      const data = await notificationsApi.list({ limit: 50 });
      setNotifications(data.notifications || []);
      setUnreadCount(data.unread_count || 0);
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleMarkRead = async (id) => {
    try {
      await notificationsApi.markRead(id);
      // Update local state
      setNotifications(prev => 
        prev.map(n => 
          n.id === id ? { ...n, is_read: true, read_at: new Date().toISOString() } : n
        )
      );
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await notificationsApi.markAllRead();
      setNotifications(prev => 
        prev.map(n => ({ ...n, is_read: true, read_at: new Date().toISOString() }))
      );
      setUnreadCount(0);
    } catch (error) {
      console.error('Failed to mark all as read:', error);
    }
  };

  const handleDelete = async (id) => {
    try {
      await notificationsApi.delete(id);
      const deleted = notifications.find(n => n.id === id);
      setNotifications(prev => prev.filter(n => n.id !== id));
      if (deleted && !deleted.is_read) {
        setUnreadCount(prev => Math.max(0, prev - 1));
      }
    } catch (error) {
      console.error('Failed to delete notification:', error);
    }
  };

  const handleNotificationClick = (notification) => {
    // Mark as read if unread
    if (!notification.is_read) {
      handleMarkRead(notification.id);
    }
    
    // Navigate to task if there's a task_id in payload
    if (notification.payload?.task_id) {
      onOpenTask(notification.payload.task_id);
    }
  };

  const getIcon = (type) => {
    switch (type) {
      case 'task_assigned':
        return 'assignment';
      case 'task_mention':
        return 'mention';
      case 'task_comment':
        return 'chat_bubble';
      case 'task_due_soon':
        return 'schedule';
      case 'task_overdue':
        return 'warning';
      case 'project_invite':
        return 'group_add';
      default:
        return 'notifications';
    }
  };

  const getIconColor = (type) => {
    switch (type) {
      case 'task_assigned':
        return 'text-logic-blue';
      case 'task_mention':
        return 'text-mint-success';
      case 'task_comment':
        return 'text-terminal-indigo';
      case 'task_due_soon':
        return 'text-amber-urgency';
      case 'task_overdue':
        return 'text-error';
      case 'project_invite':
        return 'text-logic-blue';
      default:
        return 'text-text-secondary';
    }
  };

  const unreadNotifications = notifications.filter(n => !n.is_read);
  const readNotifications = notifications.filter(n => n.is_read);

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center p-6">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-logic-blue border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
          <p className="text-text-secondary">Loading notifications...</p>
        </div>
      </div>
    );
  }

  return (
    <main className="flex-1 overflow-y-auto p-6 bg-background select-none">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <div>
            <h2 className="text-3xl font-bold text-text-primary">Notifications</h2>
            <p className="text-text-secondary mt-1">
              {unreadCount > 0 ? `${unreadCount} unread notifications` : 'All caught up!'}
            </p>
          </div>
          <div className="flex gap-2">
            {unreadCount > 0 && (
              <button
                onClick={handleMarkAllRead}
                className="px-4 py-2 bg-logic-blue text-white rounded-lg font-medium hover:bg-logic-blue-dark transition flex items-center gap-2"
              >
                <span className="material-symbols-outlined text-lg">done_all</span>
                Mark All Read
              </button>
            )}
            <button
              onClick={fetchNotifications}
              className="px-4 py-2 bg-white border border-border rounded-lg font-medium hover:bg-surface-hover transition flex items-center gap-2"
            >
              <span className="material-symbols-outlined text-lg">refresh</span>
              Refresh
            </button>
          </div>
        </div>

        {/* Unread Section */}
        {unreadNotifications.length > 0 && (
          <div className="mb-6">
            <h3 className="text-sm font-semibold text-text-secondary uppercase tracking-wider mb-3">
              Unread ({unreadNotifications.length})
            </h3>
            <div className="space-y-2">
              {unreadNotifications.map((notification) => (
                <NotificationCard
                  key={notification.id}
                  notification={notification}
                  onMarkRead={handleMarkRead}
                  onDelete={handleDelete}
                  onClick={() => handleNotificationClick(notification)}
                  getIcon={getIcon}
                  getIconColor={getIconColor}
                />
              ))}
            </div>
          </div>
        )}

        {/* Read Section */}
        {readNotifications.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-text-secondary uppercase tracking-wider mb-3">
              Earlier
            </h3>
            <div className="space-y-2 opacity-80 hover:opacity-100 transition-opacity">
              {readNotifications.map((notification) => (
                <NotificationCard
                  key={notification.id}
                  notification={notification}
                  onMarkRead={handleMarkRead}
                  onDelete={handleDelete}
                  onClick={() => handleNotificationClick(notification)}
                  getIcon={getIcon}
                  getIconColor={getIconColor}
                  isRead
                />
              ))}
            </div>
          </div>
        )}

        {/* Empty State */}
        {notifications.length === 0 && (
          <div className="text-center py-16 bg-white border border-border rounded-lg">
            <span className="material-symbols-outlined text-5xl text-mint-success">done_all</span>
            <h3 className="text-xl font-semibold text-text-primary mt-3">All caught up!</h3>
            <p className="text-text-secondary mt-1">No notifications at the moment</p>
          </div>
        )}
      </div>
    </main>
  );
};

/**
 * Notification Card Component
 */
const NotificationCard = ({ 
  notification, 
  onMarkRead, 
  onDelete, 
  onClick, 
  getIcon, 
  getIconColor,
  isRead = false 
}) => {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <div
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={onClick}
      className={`bg-white border border-border rounded-lg p-4 hover:shadow-md transition-all cursor-pointer ${
        !isRead ? 'border-l-4 border-l-logic-blue' : ''
      }`}
    >
      <div className="flex items-start gap-4">
        {/* Icon */}
        <div className={`w-10 h-10 rounded-full bg-surface-hover flex items-center justify-center shrink-0 ${getIconColor(notification.type)}`}>
          <span className="material-symbols-outlined">
            {getIcon(notification.type)}
          </span>
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="font-medium text-text-primary">
                {notification.title}
              </p>
              <p className="text-sm text-text-secondary mt-0.5">
                {notification.message}
              </p>
              {notification.payload?.task_title && (
                <p className="text-xs text-text-muted mt-1 font-mono">
                  Task: {notification.payload.task_title}
                </p>
              )}
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <span className="text-xs text-text-muted whitespace-nowrap">
                {notification.time_ago}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Action Buttons (on hover) */}
      {isHovered && (
        <div className="flex justify-end gap-2 mt-2 pt-2 border-t border-border">
          {!isRead && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onMarkRead(notification.id);
              }}
              className="text-xs text-logic-blue hover:underline"
            >
              Mark as read
            </button>
          )}
          <button
            onClick={(e) => {
              e.stopPropagation();
              onDelete(notification.id);
            }}
            className="text-xs text-error hover:underline"
          >
            Delete
          </button>
        </div>
      )}
    </div>
  );
};
