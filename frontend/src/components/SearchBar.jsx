import React from 'react';

export default function SearchBar({ value, onChange, onSearch, loading }) {
  const handleSubmit = (e) => {
    e.preventDefault();
    onSearch(value);
  };

  return (
    <form onSubmit={handleSubmit} className="search-container">
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Search for research papers... (e.g., 'machine learning in healthcare')"
        className="search-input input"
        disabled={loading}
        data-testid="search-input"
      />
      <button
        type="submit"
        disabled={loading || !value.trim()}
        className="btn btn-primary search-button"
        data-testid="search-btn"
      >
        {loading ? (
          <>
            <div className="spinner-sm"></div>
            <span>Searching...</span>
          </>
        ) : (
          <>
            <svg className="w-5 h-5" style={{ width: '1.25rem', height: '1.25rem' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <span>Search</span>
          </>
        )}
      </button>
    </form>
  );
}
