/**
 * Side Navigation Component
 * 
 * Main navigation sidebar with icons and labels.
 */

import React from 'react';

export const SideNav = ({
  currentView,
  onNavigate,
  onCreateBoard,
  unreadCount,
  user,
  onLogout,
}) => {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: 'dashboard' },
    { id: 'my-tasks', label: 'My Tasks', icon: 'assignment_turned_in' },
    { id: 'boards', label: 'Boards', icon: 'view_kanban' },
    { id: 'notifications', label: 'Notifications', icon: 'notifications', badge: unreadCount },
  ];

  return (
    <aside className="w-60 h-full fixed left-0 top-0 bg-white border-r border-border flex flex-col py-6 px-3 z-50 select-none">
      {/* Brand */}
      <div
        onClick={() => onNavigate('dashboard')}
        className="flex items-center gap-3 mb-6 px-2 cursor-pointer group"
      >
        <div className="w-8 h-8 rounded bg-terminal-indigo flex items-center justify-center text-white group-hover:bg-logic-blue transition-colors">
          <span className="material-symbols-outlined text-lg">grid_view</span>
        </div>
        <div>
          <h1 className="text-xl font-bold text-terminal-indigo">TeamUp</h1>
          <p className="text-xs text-text-secondary">Collaborative Workspace</p>
        </div>
      </div>

      {/* Create Board Button */}
      <button
        onClick={onCreateBoard}
        className="w-full bg-logic-blue text-white rounded-lg font-medium py-2.5 px-4 mb-5 hover:bg-logic-blue-dark transition flex items-center justify-center gap-2"
      >
        <span className="material-symbols-outlined text-lg">add</span>
        <span>Create New Board</span>
      </button>

      {/* Navigation */}
      <nav className="flex-1 flex flex-col gap-1 overflow-y-auto">
        {navItems.map((item) => (
          <button
            key={item.id}
            onClick={() => onNavigate(item.id)}
            className={`flex items-center justify-between w-full px-3 py-2 rounded-lg text-sm font-medium transition text-left ${
              currentView === item.id
                ? 'text-secondary bg-surface-hover border-r-2 border-secondary'
                : 'text-text-secondary hover:bg-surface-hover hover:text-text-primary'
            }`}
          >
            <div className="flex items-center gap-3">
              <span className={`material-symbols-outlined text-xl ${currentView === item.id ? 'fill' : ''}`}>
                {item.icon}
              </span>
              <span>{item.label}</span>
            </div>
            {item.badge > 0 && (
              <span className="bg-logic-blue text-white text-xs font-bold px-1.5 py-0.5 rounded-full">
                {item.badge}
              </span>
            )}
          </button>
        ))}
      </nav>

      {/* Footer */}
      <div className="mt-auto pt-4 border-t border-border flex flex-col gap-1">
        <button
          onClick={() => onNavigate('settings')}
          className="flex items-center gap-3 px-3 py-2 text-text-secondary hover:bg-surface-hover rounded-lg transition text-sm text-left"
        >
          <span className="material-symbols-outlined text-xl">settings</span>
          <span>Settings</span>
        </button>
        <button
          onClick={onLogout}
          className="flex items-center gap-3 px-3 py-2 text-text-secondary hover:bg-error-light hover:text-error rounded-lg transition text-sm text-left"
        >
          <span className="material-symbols-outlined text-xl">logout</span>
          <span>Sign Out</span>
        </button>
      </div>
    </aside>
  );
};
