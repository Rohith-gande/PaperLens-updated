import React from 'react';

export default function HistorySidebar({ show, papers, onSelectPaper, onClose }) {
  if (!show) return null;

  return (
    <>
      {/* Backdrop for mobile */}
      <div 
        className={`sidebar-backdrop ${show ? 'sidebar-backdrop-visible' : ''}`}
        onClick={onClose}
      ></div>
      
      {/* Sidebar */}
      <div className={`sidebar ${show ? 'sidebar-open' : ''}`} data-testid="history-sidebar">
        <div className="sidebar-header">
          <h2 className="sidebar-title">Your Papers</h2>
          <button
            onClick={onClose}
            className="btn-icon btn-ghost"
            data-testid="close-history-btn"
          >
            <svg style={{ width: '1.25rem', height: '1.25rem' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="sidebar-body">
          {papers.length === 0 ? (
            <div className="sidebar-empty">
              <svg className="sidebar-empty-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <p style={{ fontWeight: 'var(--font-weight-medium)' }}>No papers yet</p>
              <p style={{ fontSize: 'var(--font-size-sm)', marginTop: 'var(--spacing-xs)' }}>Search and explore papers to build your history</p>
            </div>
          ) : (
            <div className="sidebar-section">
              {papers.map((item, index) => {
                const paper = item.paper || item;
                return (
                  <div
                    key={index}
                    className="sidebar-item"
                    onClick={() => onSelectPaper(paper)}
                    data-testid="history-paper-item"
                  >
                    <h3 className="sidebar-item-title">
                      {paper.title}
                    </h3>
                    <div className="sidebar-item-meta">
                      {paper.year && <span>{paper.year}</span>}
                      {paper.year && item.saved_at && <span> • </span>}
                      {item.saved_at && (
                        <span>
                          {new Date(item.saved_at).toLocaleDateString()}
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </>
  );
}
