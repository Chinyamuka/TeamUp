/**
 * Button Component
 * 
 * Reusable button with variants.
 */

import React from 'react';

export const Button = ({
  children,
  variant = 'primary',
  size = 'md',
  className = '',
  disabled = false,
  onClick,
  ...props
}) => {
  const baseStyles = 'inline-flex items-center justify-center gap-1.5 font-medium rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed';
  
  const variants = {
    primary: 'bg-logic-blue text-white hover:bg-logic-blue-dark',
    secondary: 'bg-surface-hover text-text-primary hover:bg-border',
    outline: 'border border-border text-text-primary hover:bg-surface-hover',
    danger: 'bg-error text-white hover:bg-error/90',
    ghost: 'text-text-secondary hover:bg-surface-hover',
  };

  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-sm',
    lg: 'px-6 py-2.5 text-base',
  };

  return (
    <button
      className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`}
      disabled={disabled}
      onClick={onClick}
      {...props}
    >
      {children}
    </button>
  );
};
