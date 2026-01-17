import React, { useState, useEffect } from 'react';
import { listEvents, createEvent, getBriefing, closeEvent, listPeople } from '../api';
import WarningBox from '../components/WarningBox';
import JsonBox from '../components/JsonBox';

export default function Events() {
  const [events, setEvents] = useState([]);
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [briefing, setBriefing] = useState(null);
  const [selectedItems, setSelectedItems] = useState(new Set());
  const [people, setPeople] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [eventTitle, setEventTitle] = useState('');
  const [selectedPerson, setSelectedPerson] = useState('');

  useEffect(() => {
    loadEvents();
    loadPeople();
  }, []);

  useEffect(() => {
    if (selectedEvent) {
      loadBriefing();
    } else {
      setBriefing(null);
      setSelectedItems(new Set());
    }
  }, [selectedEvent]);

  const loadEvents = async () => {
    setLoading(true);
    setError(null);
    try {
      const eventsList = await listEvents();
      setEvents(eventsList);
    } catch (err) {
      // Endpoint might not exist
      setEvents([]);
      setError('Endpoint de eventos no disponible. Puedes crear eventos manualmente.');
    } finally {
      setLoading(false);
    }
  };

  const loadPeople = async () => {
    try {
      const peopleList = await listPeople();
      setPeople(peopleList);
    } catch (err) {
      // Ignore
    }
  };

  const loadBriefing = async () => {
    if (!selectedEvent) return;

    setLoading(true);
    setError(null);

    try {
      const briefingData = await getBriefing(selectedEvent.id);
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
      
      setEventTitle('');
      setSelectedPerson('');
      setShowCreateForm(false);
      await loadEvents();
      setSelectedEvent(event);
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

    setLoading(true);
    setError(null);

    try {
      const result = await closeEvent(selectedEvent.id, Array.from(selectedItems));
      alert(`✅ ${result.closed} item(s) cerrado(s)`);
      setSelectedItems(new Set());
      await loadBriefing();
      await loadEvents();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getEventStatus = (event) => {
    const now = new Date();
    const start = new Date(event.start_time);
    const end = new Date(event.end_time);
    
    if (now < start) return { label: 'Upcoming', color: '#17a2b8' };
    if (now >= start && now <= end) return { label: 'Ongoing', color: '#ffc107' };
    return { label: 'Past', color: '#6c757d' };
  };

  return (
    <div>
      <h2>Timeline / Eventos — "¿Entiendo el tiempo?"</h2>

      {error && <div className="error">Error: {error}</div>}

      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3>Eventos</h3>
          <button onClick={() => setShowCreateForm(!showCreateForm)}>
            {showCreateForm ? 'Cancelar' : '+ Crear Evento'}
          </button>
        </div>

        {showCreateForm && (
          <form onSubmit={handleCreateEvent} style={{ marginTop: '15px', padding: '15px', background: '#f8f9fa', borderRadius: '4px' }}>
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
              {loading ? 'Creando...' : 'Crear Evento'}
            </button>
          </form>
        )}
      </div>

      {events.length === 0 && !loading && (
        <WarningBox 
          message="No hay eventos. Crea uno para comenzar." 
          type="info" 
        />
      )}

      <div className="card">
        <h3>Lista de Eventos</h3>
        {loading ? (
          <div>Cargando...</div>
        ) : (
          <div>
            {events.map(event => {
              const status = getEventStatus(event);
              return (
                <div
                  key={event.id}
                  onClick={() => setSelectedEvent(event)}
                  style={{
                    padding: '15px',
                    margin: '5px 0',
                    background: selectedEvent?.id === event.id ? '#e7f3ff' : '#f8f9fa',
                    border: '1px solid #ddd',
                    borderRadius: '4px',
                    cursor: 'pointer',
                  }}
                >
                  <div style={{ fontWeight: 'bold', marginBottom: '5px' }}>
                    {event.title}
                  </div>
                  <div style={{ fontSize: '12px', color: '#666' }}>
                    Persona: {event.person_name || 'Sin persona'} | 
                    Fecha: {new Date(event.start_time).toLocaleString('es-ES')} | 
                    <span style={{ color: status.color, fontWeight: 'bold' }}>
                      {' '}{status.label}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {selectedEvent && (
        <div>
          <div className="card">
            <h3>Detalle del Evento</h3>
            <div style={{ marginBottom: '10px' }}>
              <strong>Título:</strong> {selectedEvent.title}
            </div>
            <div style={{ marginBottom: '10px' }}>
              <strong>Persona:</strong> {selectedEvent.person_name || 'Sin persona'}
            </div>
            <div style={{ marginBottom: '10px' }}>
              <strong>Inicio:</strong> {new Date(selectedEvent.start_time).toLocaleString('es-ES')}
            </div>
            <div style={{ marginBottom: '10px' }}>
              <strong>Fin:</strong> {new Date(selectedEvent.end_time).toLocaleString('es-ES')}
            </div>
            <button onClick={loadBriefing} disabled={loading} style={{ marginTop: '10px' }}>
              {loading ? 'Cargando...' : '🔄 Cargar Briefing'}
            </button>
          </div>

          {briefing && (
            <div className="card">
              <h3>Briefing & Cierre — "¿Cierro loops o acumulo basura?"</h3>
              
              {briefing.briefing && briefing.briefing.length > 0 ? (
                <div>
                  {briefing.briefing.length > 10 && (
                    <WarningBox 
                      message={`⚠️ Hay ${briefing.briefing.length} items pendientes. Considera priorizar.`}
                      type="warning"
                    />
                  )}
                  
                  <h4>Items Pendientes ({briefing.briefing.length}):</h4>
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
                      }}
                      onClick={() => handleToggleItem(item.id)}
                    >
                      <input
                        type="checkbox"
                        checked={selectedItems.has(item.id)}
                        onChange={() => handleToggleItem(item.id)}
                        style={{ marginRight: '10px' }}
                      />
                      {item.content}
                    </div>
                  ))}
                  
                  <button
                    onClick={handleCloseEvent}
                    disabled={loading || selectedItems.size === 0}
                    style={{ marginTop: '15px', background: '#28a745' }}
                  >
                    {loading ? 'Cerrando...' : `Cerrar ${selectedItems.size} Item(s)`}
                  </button>
                </div>
              ) : (
                <WarningBox 
                  message="✅ No hay items pendientes para esta reunión. El loop está cerrado."
                  type="info"
                />
              )}
            </div>
          )}

          {briefing && <JsonBox data={briefing} title="Briefing (JSON)" />}
        </div>
      )}
    </div>
  );
}
