/**
 * Input Component
 * 
 * Reusable input with label and error.
 */

import React from 'react';

export const Input = ({
  label,
  id,
  type = 'text',
  value,
  onChange,
  placeholder,
  error,
  required = false,
  className = '',
  ...props
}) => {
  return (
    <div className={className}>
      {label && (
        <label htmlFor={id} className="block text-sm font-semibold text-text-primary mb-1">
          {label} {required && <span className="text-error">*</span>}
        </label>
      )}
      <input
        id={id}
        type={type}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        required={required}
        className={`w-full bg-surface-hover border ${error ? 'border-error' : 'border-border'} rounded-lg px-4 py-2 focus:border-logic-blue focus:ring-2 focus:ring-logic-blue/20 outline-none transition ${
          error ? 'focus:border-error focus:ring-error/20' : ''
        }`}
        {...props}
      />
      {error && <p className="mt-1 text-sm text-error">{error}</p>}
    </div>
  );
};
