/**
 * Loading Spinner Component
 */

import React from 'react';

export const LoadingSpinner = ({ size = 'md', text = 'Loading...' }) => {
  const sizes = {
    sm: 'w-6 h-6',
    md: 'w-10 h-10',
    lg: 'w-16 h-16',
  };

  return (
    <div className="flex flex-col items-center justify-center p-8">
      <div className={`${sizes[size]} border-4 border-logic-blue border-t-transparent rounded-full animate-spin`} />
      <p className="mt-4 text-text-secondary text-sm">{text}</p>
    </div>
  );
};
