import React, { useState } from 'react';
import Inbox from './pages/Inbox';
import People from './pages/People';
import Events from './pages/Events';
import Outbox from './pages/Outbox';

export default function App() {
  const [currentPage, setCurrentPage] = useState('inbox');

  return (
    <div>
      <h1>My Memory - Testing Cognitivo</h1>
      <p style={{ color: '#666', fontSize: '14px', marginBottom: '20px' }}>
        Frontend de testing para observar cómo piensa el sistema. El backend es la única fuente de verdad.
      </p>
      
      <div className="nav">
        <button
          className={currentPage === 'inbox' ? 'active' : ''}
          onClick={() => setCurrentPage('inbox')}
        >
          Inbox
        </button>
        <button
          className={currentPage === 'people' ? 'active' : ''}
          onClick={() => setCurrentPage('people')}
        >
          People
        </button>
        <button
          className={currentPage === 'events' ? 'active' : ''}
          onClick={() => setCurrentPage('events')}
        >
          Events
        </button>
        <button
          className={currentPage === 'outbox' ? 'active' : ''}
          onClick={() => setCurrentPage('outbox')}
        >
          Outbox
        </button>
      </div>

      {currentPage === 'inbox' && <Inbox />}
      {currentPage === 'people' && <People />}
      {currentPage === 'events' && <Events />}
      {currentPage === 'outbox' && <Outbox />}
    </div>
  );
}
