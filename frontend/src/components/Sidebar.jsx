import React from 'react';

export default function Sidebar({ currentPage, onPageChange }) {
  const pages = [
    { id: 'inbox', label: '📥 Inbox', icon: '📥' },
    { id: 'people', label: '👥 Personas', icon: '👥' },
    { id: 'meetings', label: '📅 Reuniones', icon: '📅' },
    { id: 'outbox', label: '📤 Outbox', icon: '📤' },
    { id: 'promptlab', label: '🧪 Prompt Lab', icon: '🧪' },
    { id: 'debug', label: '🐛 Debug', icon: '🐛' },
  ];

  return (
    <div style={{
      width: '200px',
      background: '#2c3e50',
      color: 'white',
      padding: '20px',
      minHeight: '100vh',
      position: 'fixed',
      left: 0,
      top: 0,
    }}>
      <h2 style={{ marginBottom: '30px', fontSize: '18px', fontWeight: 'bold' }}>
        Control Panel
      </h2>
      <nav style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {pages.map(page => (
          <button
            key={page.id}
            onClick={() => onPageChange(page.id)}
            style={{
              padding: '12px 15px',
              background: currentPage === page.id ? '#3498db' : 'transparent',
              border: 'none',
              color: 'white',
              textAlign: 'left',
              cursor: 'pointer',
              borderRadius: '4px',
              fontSize: '14px',
              transition: 'background 0.2s',
            }}
            onMouseEnter={(e) => {
              if (currentPage !== page.id) e.target.style.background = '#34495e';
            }}
            onMouseLeave={(e) => {
              if (currentPage !== page.id) e.target.style.background = 'transparent';
            }}
          >
            {page.label}
          </button>
        ))}
      </nav>
    </div>
  );
}
