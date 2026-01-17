import React from 'react';

export default function WarningBox({ message, type = 'warning' }) {
  if (!message) return null;
  
  const styles = {
    warning: {
      background: '#fff3cd',
      border: '1px solid #ffc107',
      color: '#856404',
    },
    info: {
      background: '#d1ecf1',
      border: '1px solid #17a2b8',
      color: '#0c5460',
    },
    error: {
      background: '#f8d7da',
      border: '1px solid #dc3545',
      color: '#721c24',
    },
  };
  
  return (
    <div style={{
      padding: '15px',
      borderRadius: '4px',
      margin: '10px 0',
      ...styles[type],
    }}>
      {message}
    </div>
  );
}
