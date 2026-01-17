import React from 'react';

export default function JsonBox({ data, title = null }) {
  if (!data) return null;
  
  return (
    <div className="card">
      {title && <h3>{title}</h3>}
      <pre style={{
        background: '#f8f9fa',
        padding: '15px',
        borderRadius: '4px',
        overflow: 'auto',
        fontSize: '12px',
        maxHeight: '400px',
      }}>
        {JSON.stringify(data, null, 2)}
      </pre>
    </div>
  );
}
