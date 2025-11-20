import React from "react";

export default function History({ history, onSelect }) {
  return (
    <div style={{ background: 'var(--bg-tertiary)', padding: 'var(--spacing-md)', height: '100%' }}>
      <h2 style={{ fontSize: 'var(--font-size-lg)', fontWeight: 'var(--font-weight-semibold)', marginBottom: 'var(--spacing-md)' }}>History</h2>
      <ul style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-sm)' }}>
        {history.map((item, index) => (
          <li
            key={index}
            className="sidebar-item"
            onClick={() => onSelect(item)}
          >
            {item.query}
          </li>
        ))}
      </ul>
    </div>
  );
}
