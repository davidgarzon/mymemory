import React from 'react';

export default function List({ items, renderItem, emptyMessage = "No hay items" }) {
  if (!items || items.length === 0) {
    return <div style={{ color: '#666', fontStyle: 'italic' }}>{emptyMessage}</div>;
  }
  
  return (
    <div>
      {items.map((item, index) => (
        <div key={item.id || index}>
          {renderItem(item)}
        </div>
      ))}
    </div>
  );
}
