import React, { useState, useEffect } from 'react';
import { listPeople, getBriefingForPerson, closeBriefing } from '../api';

export default function Briefing() {
  const [people, setPeople] = useState([]);
  const [selectedPersonId, setSelectedPersonId] = useState('');
  const [briefing, setBriefing] = useState(null);
  const [selectedItems, setSelectedItems] = useState(new Set());
  const [loading, setLoading] = useState(false);
  const [closing, setClosing] = useState(false);
  const [error, setError] = useState(null);

  // Load people on mount
  useEffect(() => {
    loadPeople();
  }, []);

  // Load briefing when person changes
  useEffect(() => {
    if (selectedPersonId) {
      loadBriefing(selectedPersonId);
    } else {
      setBriefing(null);
      setSelectedItems(new Set());
    }
  }, [selectedPersonId]);

  const loadPeople = async () => {
    setLoading(true);
    setError(null);
    try {
      const peopleData = await listPeople();
      setPeople(peopleData);
    } catch (err) {
      setError(`Error cargando personas: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const loadBriefing = async (personId) => {
    setLoading(true);
    setError(null);
    try {
      const briefingData = await getBriefingForPerson(personId);
      setBriefing(briefingData);
      setSelectedItems(new Set()); // Reset selections when loading new briefing
    } catch (err) {
      setError(`Error cargando briefing: ${err.message}`);
      setBriefing(null);
    } finally {
      setLoading(false);
    }
  };

  const handleItemToggle = (itemId) => {
    const newSelected = new Set(selectedItems);
    if (newSelected.has(itemId)) {
      newSelected.delete(itemId);
    } else {
      newSelected.add(itemId);
    }
    setSelectedItems(newSelected);
  };

  const handleCloseItems = async () => {
    if (!selectedPersonId || selectedItems.size === 0) return;

    setClosing(true);
    setError(null);
    try {
      const itemIdsArray = Array.from(selectedItems);
      await closeBriefing(selectedPersonId, itemIdsArray);
      
      // Reload briefing after closing
      await loadBriefing(selectedPersonId);
      
      // Clear selections
      setSelectedItems(new Set());
    } catch (err) {
      setError(`Error cerrando temas: ${err.message}`);
    } finally {
      setClosing(false);
    }
  };

  const formatDate = (dateString) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('es-ES', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateString;
    }
  };

  return (
    <div>
      <h1>📋 Briefing</h1>
      <p style={{ color: '#666', marginBottom: '20px' }}>
        Prepara y cierra reuniones con personas
      </p>

      {error && (
        <div className="error" style={{ marginBottom: '20px' }}>
          {error}
        </div>
      )}

      {/* Person selector */}
      <div className="card" style={{ marginBottom: '20px' }}>
        <label style={{ 
          display: 'block', 
          marginBottom: '12px', 
          fontWeight: '600',
          color: '#333',
          fontSize: '15px'
        }}>
          Seleccionar persona:
        </label>
        <select
          value={selectedPersonId}
          onChange={(e) => setSelectedPersonId(e.target.value)}
          disabled={loading}
          style={{
            width: '100%',
            padding: '12px',
            fontSize: '15px',
            border: '1px solid #ddd',
            borderRadius: '6px',
            background: 'white',
            cursor: loading ? 'not-allowed' : 'pointer',
          }}
        >
          <option value="">-- Selecciona una persona --</option>
          {people.map(person => (
            <option key={person.id} value={person.id}>
              {person.name || person.display_name}
            </option>
          ))}
        </select>
      </div>

      {loading && !briefing && (
        <div className="card">
          <p>Cargando...</p>
        </div>
      )}

      {briefing && (
        <>
          {/* Pending items */}
          <div className="card" style={{ marginBottom: '20px' }}>
            <h2 style={{ 
              marginBottom: '20px', 
              fontSize: '20px', 
              color: '#333',
              borderBottom: '2px solid #007bff',
              paddingBottom: '8px'
            }}>
              Temas pendientes
            </h2>
            {briefing.pending_items && briefing.pending_items.length > 0 ? (
              <div style={{ marginBottom: '20px' }}>
                {briefing.pending_items.map(item => (
                  <div
                    key={item.id}
                    onClick={() => handleItemToggle(item.id)}
                    style={{
                      padding: '14px',
                      marginBottom: '10px',
                      border: selectedItems.has(item.id) ? '2px solid #28a745' : '1px solid #ddd',
                      borderRadius: '6px',
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: '12px',
                      background: selectedItems.has(item.id) ? '#f0fff4' : 'white',
                      cursor: 'pointer',
                      transition: 'all 0.2s ease',
                    }}
                    onMouseEnter={(e) => {
                      if (!selectedItems.has(item.id)) {
                        e.currentTarget.style.borderColor = '#007bff';
                        e.currentTarget.style.background = '#f8f9fa';
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (!selectedItems.has(item.id)) {
                        e.currentTarget.style.borderColor = '#ddd';
                        e.currentTarget.style.background = 'white';
                      }
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={selectedItems.has(item.id)}
                      onChange={() => handleItemToggle(item.id)}
                      onClick={(e) => e.stopPropagation()}
                      style={{ 
                        marginTop: '2px',
                        width: '18px',
                        height: '18px',
                        cursor: 'pointer'
                      }}
                    />
                    <div style={{ flex: 1 }}>
                      <div style={{ 
                        fontWeight: '500', 
                        marginBottom: '6px',
                        color: '#333',
                        fontSize: '15px'
                      }}>
                        {item.content}
                      </div>
                      <div style={{ 
                        fontSize: '12px', 
                        color: '#888'
                      }}>
                        Creado: {formatDate(item.created_at)}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ 
                color: '#888', 
                fontStyle: 'italic',
                padding: '20px',
                textAlign: 'center',
                background: '#f8f9fa',
                borderRadius: '4px'
              }}>
                No hay temas pendientes para esta persona
              </p>
            )}

            {/* Close button */}
            {briefing.pending_items && briefing.pending_items.length > 0 && (
              <div style={{ 
                marginTop: '20px',
                paddingTop: '20px',
                borderTop: '1px solid #e0e0e0'
              }}>
                <button
                  onClick={handleCloseItems}
                  disabled={selectedItems.size === 0 || closing}
                  style={{
                    background: selectedItems.size > 0 ? '#28a745' : '#ccc',
                    color: 'white',
                    border: 'none',
                    padding: '12px 24px',
                    borderRadius: '6px',
                    cursor: selectedItems.size > 0 ? 'pointer' : 'not-allowed',
                    fontSize: '15px',
                    fontWeight: '500',
                    transition: 'background 0.2s ease',
                    width: '100%',
                    maxWidth: '400px',
                  }}
                  onMouseEnter={(e) => {
                    if (selectedItems.size > 0 && !closing) {
                      e.currentTarget.style.background = '#218838';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (selectedItems.size > 0 && !closing) {
                      e.currentTarget.style.background = '#28a745';
                    }
                  }}
                >
                  {closing ? 'Cerrando...' : `Cerrar temas seleccionados (${selectedItems.size})`}
                </button>
              </div>
            )}
          </div>

          {/* Recent discussed */}
          <div className="card">
            <h2 style={{ 
              marginBottom: '20px', 
              fontSize: '20px', 
              color: '#333',
              borderBottom: '2px solid #28a745',
              paddingBottom: '8px'
            }}>
              Últimos temas discutidos
            </h2>
            {briefing.recent_discussed && briefing.recent_discussed.length > 0 ? (
              <div>
                {briefing.recent_discussed.map(item => (
                  <div
                    key={item.id}
                    style={{
                      padding: '14px',
                      marginBottom: '10px',
                      border: '1px solid #d4edda',
                      borderRadius: '6px',
                      background: '#f8fff9',
                      borderLeft: '4px solid #28a745',
                    }}
                  >
                    <div style={{ 
                      fontWeight: '500', 
                      marginBottom: '6px',
                      color: '#333',
                      fontSize: '15px'
                    }}>
                      {item.content}
                    </div>
                    <div style={{ 
                      fontSize: '12px', 
                      color: '#888'
                    }}>
                      Discutido: {formatDate(item.discussed_at)}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ 
                color: '#888', 
                fontStyle: 'italic',
                padding: '20px',
                textAlign: 'center',
                background: '#f8f9fa',
                borderRadius: '4px'
              }}>
                No hay temas discutidos recientemente
              </p>
            )}
          </div>
        </>
      )}
    </div>
  );
}
