/**
 * PermissionGuard Component
 * 
 * Wraps content that should only be shown to users with a specific role.
 */

import React from 'react';

const ROLE_HIERARCHY = {
  owner: 4,
  admin: 3,
  member: 2,
  viewer: 1
};

const hasRole = (userRole, requiredRole) => {
  if (!userRole) return false;
  return (ROLE_HIERARCHY[userRole] || 0) >= (ROLE_HIERARCHY[requiredRole] || 0);
};

export const PermissionGuard = ({ 
  userRole, 
  requiredRole, 
  children, 
  fallback = null 
}) => {
  if (hasRole(userRole, requiredRole)) {
    return <>{children}</>;
  }
  return <>{fallback}</>;
};

/**
 * Higher-order component for role-based rendering
 */
export const withPermission = (WrappedComponent, requiredRole) => {
  return function WithPermissionComponent({ userRole, ...props }) {
    if (hasRole(userRole, requiredRole)) {
      return <WrappedComponent {...props} />;
    }
    return null;
  };
};
