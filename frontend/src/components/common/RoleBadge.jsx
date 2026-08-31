/**
 * RoleBadge Component
 * 
 * Displays a user's role with color coding and icon.
 */

import React from 'react';

// Role helpers
const ROLE_HIERARCHY = {
  owner: 4,
  admin: 3,
  member: 2,
  viewer: 1
};

const getRoleDisplay = (role) => {
  const names = {
    owner: 'Owner',
    admin: 'Admin',
    member: 'Member',
    viewer: 'Viewer'
  };
  return names[role] || role;
};

const getRoleColor = (role) => {
  const colors = {
    owner: 'bg-amber-urgency text-black',
    admin: 'bg-logic-blue text-white',
    member: 'bg-mint-success text-white',
    viewer: 'bg-gray-400 text-white'
  };
  return colors[role] || 'bg-gray-200 text-gray-600';
};

const getRoleIcon = (role) => {
  const icons = {
    owner: 'stars',
    admin: 'shield',
    member: 'person',
    viewer: 'visibility'
  };
  return icons[role] || 'person';
};

export const RoleBadge = ({ role, className = '', size = 'sm' }) => {
  if (!role) return null;
  
  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5 gap-0.5',
    md: 'text-sm px-2.5 py-1 gap-1',
    lg: 'text-base px-3 py-1.5 gap-1'
  };
  
  return (
    <span 
      className={`inline-flex items-center rounded-full font-medium ${getRoleColor(role)} ${sizeClasses[size]} ${className}`}
    >
      <span className="material-symbols-outlined text-[inherit]">
        {getRoleIcon(role)}
      </span>
      {getRoleDisplay(role)}
    </span>
  );
};
