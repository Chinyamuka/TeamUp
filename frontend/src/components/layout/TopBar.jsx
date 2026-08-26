/**
 * Top Bar Component
 * 
 * Displays current view, search, user avatar, and notifications.
 */

import React, { useState } from 'react';

export const TopBar = ({
  currentView,
  onNavigate,
  user,
  unreadCount,
  onNotificationClick,
}) => {
  const [showProfile, setShowProfile] = useState(false);

  const viewTitles = {
    dashboard: 'Dashboard',
    'my-tasks': 'My Tasks',
    boards: 'Boards',
    notifications: 'Notifications',
  };

  return (
    <header className="bg-background border-b border-border sticky top-0 z-40 flex justify-between items-center h-16 px-6 select-none">
      {/* Left: Title */}
      <div>
        <h1 className="text-xl font-bold text-text-primary">
          {viewTitles[currentView] || 'TeamUp'}
        </h1>
      </div>

      {/* Right: Actions */}
      <div className="flex items-center gap-3">
        {/* Notifications */}
        <button
          onClick={onNotificationClick}
          className="relative p-2 rounded-full hover:bg-surface-hover transition"
        >
          <span className="material-symbols-outlined text-xl text-text-secondary">
            notifications
          </span>
          {unreadCount > 0 && (
            <span className="absolute top-1.5 right-1.5 w-2.5 h-2.5 bg-mint-success rounded-full border-2 border-white"></span>
          )}
        </button>

        {/* User Avatar */}
        <div className="relative">
          <button
            onClick={() => setShowProfile(!showProfile)}
            className="w-8 h-8 rounded-full overflow-hidden border border-border hover:ring-2 hover:ring-logic-blue transition"
          >
            <img
              src={user?.avatar || `https://ui-avatars.com/api/?name=${user?.full_name || 'User'}&background=3B4AF5&color=fff`}
              alt={user?.full_name || 'User'}
              className="w-full h-full object-cover"
            />
          </button>

          {showProfile && (
            <div className="absolute right-0 mt-2 w-56 bg-white border border-border rounded-lg shadow-lg py-2 z-50">
              <div className="px-4 py-2 border-b border-border">
                <p className="font-semibold text-text-primary">{user?.full_name || 'User'}</p>
                <p className="text-xs text-text-secondary">{user?.email || ''}</p>
              </div>
              <button
                onClick={() => { onNavigate('settings'); setShowProfile(false); }}
                className="w-full text-left px-4 py-2 text-sm hover:bg-surface-hover transition flex items-center gap-2"
              >
                <span className="material-symbols-outlined text-lg">settings</span>
                Settings
              </button>
              <button
                onClick={() => { onNavigate('my-tasks'); setShowProfile(false); }}
                className="w-full text-left px-4 py-2 text-sm hover:bg-surface-hover transition flex items-center gap-2"
              >
                <span className="material-symbols-outlined text-lg">assignment_turned_in</span>
                My Tasks
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
