import React from "react";

export default function ResultCard({ paper }) {
  return (
    <div className="paper-card">
      <a
        href={paper.url}
        target="_blank"
        rel="noopener noreferrer"
        className="paper-card-title"
        style={{ color: 'var(--color-primary)', textDecoration: 'none' }}
      >
        {paper.title}
      </a>
      <div className="paper-card-meta">
        <p>Authors: {paper.authors}</p>
        <p>Year: {paper.year}</p>
      </div>
      <p className="paper-card-abstract">{paper.abstract}</p>
      {paper.score && (
        <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-tertiary)', marginTop: 'var(--spacing-sm)' }}>
          Relevance Score: {paper.score.toFixed(2)}
        </p>
      )}
    </div>
  );
}
