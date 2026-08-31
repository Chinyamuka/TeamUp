/**
 * Search Bar with Filters
 */

import React, { useState, useRef, useEffect } from 'react';

export const SearchBar = ({ onSearch, onFilter, placeholder = 'Search...' }) => {
  const [query, setQuery] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState({
    priority: 'all',
    status: 'all',
  });
  const searchRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (searchRef.current && !searchRef.current.contains(event.target)) {
        setShowFilters(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSearch = (e) => {
    const value = e.target.value;
    setQuery(value);
    if (onSearch) onSearch(value, filters);
  };

  const handleFilterChange = (key, value) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
    if (onSearch) onSearch(query, newFilters);
  };

  const hasActiveFilters = filters.priority !== 'all' || filters.status !== 'all';

  return (
    <div className="relative" ref={searchRef}>
      <div className="flex items-center bg-white border border-border rounded-lg focus-within:border-logic-blue focus-within:ring-2 focus-within:ring-logic-blue/20 transition">
        <span className="material-symbols-outlined text-text-muted ml-3">search</span>
        <input
          type="text"
          value={query}
          onChange={handleSearch}
          placeholder={placeholder}
          className="flex-1 px-3 py-2 outline-none bg-transparent text-text-primary placeholder-text-muted"
        />
        <button
          onClick={() => setShowFilters(!showFilters)}
          className={`p-2 hover:bg-surface-hover rounded-r-lg transition ${hasActiveFilters ? 'text-logic-blue' : 'text-text-muted'}`}
        >
          <span className="material-symbols-outlined">tune</span>
        </button>
        {query && (
          <button
            onClick={() => {
              setQuery('');
              if (onSearch) onSearch('', filters);
            }}
            className="p-2 text-text-muted hover:text-text-primary"
          >
            <span className="material-symbols-outlined text-sm">close</span>
          </button>
        )}
      </div>

      {showFilters && (
        <div className="absolute top-full mt-2 right-0 bg-white border border-border rounded-lg shadow-lg p-4 w-64 z-30">
          <div className="space-y-3">
            <div>
              <label className="block text-xs font-semibold text-text-secondary uppercase mb-1">Priority</label>
              <select
                value={filters.priority}
                onChange={(e) => handleFilterChange('priority', e.target.value)}
                className="w-full border border-border rounded px-2 py-1.5 text-sm focus:border-logic-blue outline-none"
              >
                <option value="all">All Priorities</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-text-secondary uppercase mb-1">Status</label>
              <select
                value={filters.status}
                onChange={(e) => handleFilterChange('status', e.target.value)}
                className="w-full border border-border rounded px-2 py-1.5 text-sm focus:border-logic-blue outline-none"
              >
                <option value="all">All Status</option>
                <option value="todo">To Do</option>
                <option value="in_progress">In Progress</option>
                <option value="review">Review</option>
                <option value="done">Done</option>
              </select>
            </div>
            <button
              onClick={() => {
                const resetFilters = { priority: 'all', status: 'all' };
                setFilters(resetFilters);
                if (onSearch) onSearch(query, resetFilters);
                setShowFilters(false);
              }}
              className="w-full text-center text-sm text-logic-blue hover:underline"
            >
              Reset Filters
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
