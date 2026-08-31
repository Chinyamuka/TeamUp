/**
 * Toast Notification Component
 */

import React, { useEffect } from 'react';

export const Toast = ({ message, type = 'success', onClose, duration = 4000 }) => {
  useEffect(() => {
    const timer = setTimeout(() => {
      if (onClose) onClose();
    }, duration);
    return () => clearTimeout(timer);
  }, [duration, onClose]);

  const styles = {
    success: 'bg-mint-success text-white',
    error: 'bg-error text-white',
    warning: 'bg-amber-urgency text-black',
    info: 'bg-logic-blue text-white',
  };

  const icons = {
    success: 'check_circle',
    error: 'error',
    warning: 'warning',
    info: 'info',
  };

  return (
    <div className={`fixed top-4 right-4 z-50 flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg animate-slideIn ${styles[type] || styles.info}`}>
      <span className="material-symbols-outlined">{icons[type] || icons.info}</span>
      <span className="text-sm font-medium">{message}</span>
      <button onClick={onClose} className="hover:opacity-70">
        <span className="material-symbols-outlined text-sm">close</span>
      </button>
    </div>
  );
};
