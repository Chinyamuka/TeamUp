/**
 * Type definitions for TeamUp Frontend
 */

// ============================================================
// ROLE TYPES
// ============================================================

/**
 * @typedef {'owner' | 'admin' | 'member' | 'viewer'} ProjectRole
 */

// ============================================================
// USER TYPES
// ============================================================

/**
 * @typedef {Object} User
 * @property {number} id - User ID
 * @property {string} email - User email
 * @property {string} full_name - User full name
 * @property {string} [role] - User's role in the current context
 * @property {string} [avatar] - Avatar URL
 * @property {boolean} [is_active] - Whether user is active
 */

// ============================================================
// PROJECT TYPES
// ============================================================

/**
 * @typedef {Object} Project
 * @property {number} id - Project ID
 * @property {string} name - Project name
 * @property {string} description - Project description
 * @property {number} owner_id - Owner user ID
 * @property {Object} owner - Owner user object
 * @property {string} user_role - Current user's role in this project
 * @property {boolean} is_archived - Whether project is archived
 * @property {string} created_at - Creation timestamp
 * @property {string} updated_at - Last update timestamp
 */

// ============================================================
// BOARD TYPES
// ============================================================

/**
 * @typedef {Object} Board
 * @property {number} id - Board ID
 * @property {number} project_id - Project ID
 * @property {string} name - Board name
 * @property {string} description - Board description
 * @property {number} position - Board position
 * @property {Array<Column>} columns - Board columns
 * @property {string} user_role - Current user's role
 * @property {boolean} is_archived - Whether board is archived
 */

// ============================================================
// COLUMN TYPES
// ============================================================

/**
 * @typedef {Object} Column
 * @property {number} id - Column ID
 * @property {number} board_id - Board ID
 * @property {string} name - Column name
 * @property {number} position - Column position
 * @property {Array<Task>} tasks - Tasks in this column
 */

// ============================================================
// TASK TYPES
// ============================================================

/**
 * @typedef {Object} Task
 * @property {number} id - Task ID
 * @property {number} column_id - Column ID
 * @property {string} title - Task title
 * @property {string} description - Task description
 * @property {string} priority - Task priority
 * @property {Array<string>} labels - Task labels
 * @property {Array<User>} assignees - Assigned users
 * @property {string} due_date - Due date
 * @property {number} position - Task position
 * @property {string} user_role - Current user's role
 * @property {boolean} is_archived - Whether task is archived
 */

// ============================================================
// PERMISSION HELPERS
// ============================================================

/**
 * Role hierarchy for permission checks
 */
export const ROLE_HIERARCHY = {
  owner: 4,
  admin: 3,
  member: 2,
  viewer: 1
};

/**
 * Check if a user has at least the required role
 */
export const hasRole = (userRole, requiredRole) => {
  if (!userRole) return false;
  return (ROLE_HIERARCHY[userRole] || 0) >= (ROLE_HIERARCHY[requiredRole] || 0);
};

/**
 * Get role display name
 */
export const getRoleDisplay = (role) => {
  const names = {
    owner: 'Owner',
    admin: 'Admin',
    member: 'Member',
    viewer: 'Viewer'
  };
  return names[role] || role;
};

/**
 * Get role color for badges
 */
export const getRoleColor = (role) => {
  const colors = {
    owner: 'bg-amber-urgency text-black',
    admin: 'bg-logic-blue text-white',
    member: 'bg-mint-success text-white',
    viewer: 'bg-gray-400 text-white'
  };
  return colors[role] || 'bg-gray-200 text-gray-600';
};

/**
 * Get role icon
 */
export const getRoleIcon = (role) => {
  const icons = {
    owner: 'stars',
    admin: 'shield',
    member: 'person',
    viewer: 'visibility'
  };
  return icons[role] || 'person';
};

/**
 * Check if user can perform an action based on role
 */
export const canPerform = (userRole, requiredRole) => {
  return hasRole(userRole, requiredRole);
};
