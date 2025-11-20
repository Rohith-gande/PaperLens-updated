import React from 'react';

export default function PaperCard({ paper, onAskQuestion, selectable = false, selected = false, onToggleSelect }) {
  const hasUrl = !!(paper?.url || paper?.pdf_url || paper?.paper?.url);
  return (
    <div className="paper-card" data-testid="paper-card">
      <div className="paper-card-header">
        {selectable && (
          <label className="paper-select" title={hasUrl ? 'Select for comparison' : 'No valid link to compare'} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginRight: '0.5rem' }}>
            <input
              type="checkbox"
              checked={selected}
              onChange={onToggleSelect}
              style={{ transform: 'scale(1.3)' }}
            />
            <span style={{ fontSize: '0.9rem', fontWeight: 600 }}>
              {selected ? 'Selected' : 'Select'}
            </span>
          </label>
        )}
        <h3 className="paper-card-title">
          {paper.title}
        </h3>
        {paper.score && (
          <span className="paper-card-badge">
            {(paper.score * 100).toFixed(0)}% match
          </span>
        )}
      </div>
      
      <div className="paper-card-meta">
        {paper.authors && (
          <div className="paper-card-meta-item">
            <svg style={{ width: '1rem', height: '1rem' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
            <span>{paper.authors}</span>
          </div>
        )}
        {paper.year && (
          <div className="paper-card-meta-item">
            <svg style={{ width: '1rem', height: '1rem' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            <span>{paper.year}</span>
          </div>
        )}
      </div>

      {paper.abstract && (
        <p className="paper-card-abstract">
          {paper.abstract}
        </p>
      )}

      <div className="paper-card-actions">
        <button
          onClick={onAskQuestion}
          className="btn btn-primary"
          data-testid="ask-question-btn"
        >
          <svg style={{ width: '1.25rem', height: '1.25rem' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
          </svg>
          <span>Ask Question</span>
        </button>
        
        {paper.url && (
          <a
            href={paper.url}
            target="_blank"
            rel="noopener noreferrer"
            className="btn btn-secondary"
            data-testid="view-paper-btn"
          >
            <svg style={{ width: '1.25rem', height: '1.25rem' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
            <span>View Paper</span>
          </a>
        )}
      </div>
    </div>
  );
}
