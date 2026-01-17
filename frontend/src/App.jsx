import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import Inbox from './pages/Inbox';
import People from './pages/People';
import Meetings from './pages/Meetings';
import Outbox from './pages/Outbox';
import PromptLab from './pages/PromptLab';
import Debug from './pages/Debug';

export default function App() {
  const [currentPage, setCurrentPage] = useState('inbox');

  const renderPage = () => {
    switch (currentPage) {
      case 'inbox':
        return <Inbox />;
      case 'people':
        return <People />;
      case 'meetings':
        return <Meetings />;
      case 'outbox':
        return <Outbox />;
      case 'promptlab':
        return <PromptLab />;
      case 'debug':
        return <Debug />;
      default:
        return <Inbox />;
    }
  };

  return (
    <div style={{ display: 'flex' }}>
      <Sidebar currentPage={currentPage} onPageChange={setCurrentPage} />
      <main style={{
        marginLeft: '200px',
        padding: '30px',
        width: 'calc(100% - 200px)',
        minHeight: '100vh',
        background: '#f5f5f5',
      }}>
        {renderPage()}
      </main>
    </div>
  );
}
