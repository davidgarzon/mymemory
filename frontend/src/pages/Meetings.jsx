import React, { useState, useEffect } from 'react';
import { createEvent, getBriefing, closeEvent, listPeople } from '../api';
import JsonBox from '../components/JsonBox';

export default function Meetings() {
  const [people, setPeople] = useState([]);
  const [selectedPerson, setSelectedPerson] = useState('');
  const [eventTitle, setEventTitle] = useState('');
  const [eventId, setEventId] = useState(null);
  const [briefing, setBriefing] = useState(null);
  const [selectedItems, setSelectedItems] = useState(new Set());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadPeople();
  }, []);

  useEffect(() => {
    if (eventId) {
      loadBriefing();
    }
  }, [eventId]);

  const loadPeople = async () => {
    try {
      const peopleList = await listPeople();
      setPeople(peopleList);
    } catch (err) {
      // Ignore
    }
  };

  const loadBriefing = async () => {
    if (!eventId) return;

    setLoading(true);
    setError(null);

    try {
      const briefingData = await getBriefing(eventId);
      setBriefing(briefingData);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateEvent = async (e) => {
    e.preventDefault();
    if (!eventTitle.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const now = new Date();
      const startTime = new Date(now.getTime() + 30 * 60000);
      const endTime = new Date(startTime.getTime() + 60 * 60000);

      const event = await createEvent(
        eventTitle,
        startTime.toISOString(),
        endTime.toISOString(),
        selectedPerson || null
      );
      
      setEventId(event.id);
      setEventTitle('');
      setSelectedPerson('');
      setBriefing(null);
      setSelectedItems(new Set());
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleItem = (itemId) => {
    const newSelected = new Set(selectedItems);
    if (newSelected.has(itemId)) {
      newSelected.delete(itemId);
    } else {
      newSelected.add(itemId);
    }
    setSelectedItems(newSelected);
  };

  const handleCloseEvent = async () => {
    if (selectedItems.size === 0) {
      alert('Selecciona al menos un item para cerrar');
      return;
    }

    if (!confirm(`¿Cerrar ${selectedItems.size} item(s) como discutidos?`)) return;

    setLoading(true);
    setError(null);

    try {
      const result = await closeEvent(eventId, Array.from(selectedItems));
      alert(`✅ ${result.closed} item(s) cerrado(s)`);
      setSelectedItems(new Set());
      await loadBriefing();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1>📅 Reuniones</h1>
      <p style={{ color: '#666', marginBottom: '20px' }}>
        Crea reuniones, genera briefings y cierra loops
      </p>

      {error && <div className="error">Error: {error}</div>}

      <div className="card">
        <h2>Crear Reunión Manual</h2>
        <form onSubmit={handleCreateEvent}>
          <input
            type="text"
            value={eventTitle}
            onChange={(e) => setEventTitle(e.target.value)}
            placeholder="Título de la reunión"
            disabled={loading}
          />
          <select
            value={selectedPerson}
            onChange={(e) => setSelectedPerson(e.target.value)}
            disabled={loading}
          >
            <option value="">Sin persona</option>
            {people.map(person => (
              <option key={person.id} value={person.name}>
                {person.name}
              </option>
            ))}
          </select>
          <button type="submit" disabled={loading || !eventTitle.trim()}>
            {loading ? 'Creando...' : 'Crear Reunión'}
          </button>
        </form>
      </div>

      {eventId && (
        <div>
          <div className="card">
            <h2>Briefing del Evento</h2>
            <div style={{ marginBottom: '15px' }}>
              <strong>Event ID:</strong> {eventId}
            </div>
            <button onClick={loadBriefing} disabled={loading}>
              {loading ? 'Cargando...' : '🔄 Generar Briefing'}
            </button>
          </div>

          {briefing && (
            <div className="card">
              <h3>Briefing (como se enviaría antes de la reunión)</h3>
              <div style={{ marginBottom: '15px', padding: '15px', background: '#f8f9fa', borderRadius: '4px' }}>
                <p><strong>Persona:</strong> {briefing.person || 'Sin persona'}</p>
                <p><strong>Items pendientes:</strong> {briefing.briefing?.length || 0}</p>
              </div>

              {briefing.briefing && briefing.briefing.length > 0 ? (
                <div>
                  <h4>Items Pendientes:</h4>
                  {briefing.briefing.map(item => (
                    <div
                      key={item.id}
                      style={{
                        padding: '10px',
                        margin: '5px 0',
                        border: '1px solid #ddd',
                        borderRadius: '4px',
                        background: selectedItems.has(item.id) ? '#e7f3ff' : 'white',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '10px',
                      }}
                      onClick={() => handleToggleItem(item.id)}
                    >
                      <input
                        type="checkbox"
                        checked={selectedItems.has(item.id)}
                        onChange={() => handleToggleItem(item.id)}
                      />
                      <span style={{ flex: 1 }}>{item.content}</span>
                    </div>
                  ))}
                  
                  <button
                    onClick={handleCloseEvent}
                    disabled={loading || selectedItems.size === 0}
                    style={{ marginTop: '15px', background: '#28a745' }}
                  >
                    {loading ? 'Cerrando...' : `Cerrar Reunión (${selectedItems.size} items)`}
                  </button>
                </div>
              ) : (
                <div style={{ color: '#666', padding: '20px', textAlign: 'center' }}>
                  ✅ No hay items pendientes para esta reunión
                </div>
              )}
            </div>
          )}

          {briefing && (
            <div className="card">
              <h3>Briefing (JSON Raw)</h3>
              <JsonBox data={briefing} title={null} />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
