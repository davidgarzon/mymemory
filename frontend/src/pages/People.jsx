import React, { useState, useEffect } from 'react';
import { listPeople, listPending, listAllItems, markItemAsDiscussed } from '../api';

export default function People() {
  const [people, setPeople] = useState([]);
  const [selectedPerson, setSelectedPerson] = useState(null);
  const [pendingItems, setPendingItems] = useState([]);
  const [discussedItems, setDiscussedItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [markingItem, setMarkingItem] = useState(null);

  useEffect(() => {
    loadPeople();
  }, []);

  useEffect(() => {
    if (selectedPerson) {
      loadPersonDetails(selectedPerson.id);
    } else {
      setPendingItems([]);
      setDiscussedItems([]);
    }
  }, [selectedPerson]);

  const loadPeople = async () => {
    try {
      const peopleList = await listPeople();
      setPeople(peopleList);
    } catch (err) {
      setError(err.message);
    }
  };

  const loadPersonDetails = async (personId) => {
    setLoading(true);
    setError(null);
    try {
      const pending = await listPending(personId);
      setPendingItems(pending);

      const allItems = await listAllItems('discussed');
      const discussed = allItems
        .filter(item => item.related_person_id === personId)
        .slice(0, 20);
      setDiscussedItems(discussed);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleMarkAsDiscussed = async (itemId) => {
    if (!confirm('¿Marcar este item como discutido? (Debug)')) return;

    setMarkingItem(itemId);
    try {
      await markItemAsDiscussed(itemId);
      await loadPersonDetails(selectedPerson.id);
      await loadPeople();
    } catch (err) {
      alert(`Error: ${err.message}`);
    } finally {
      setMarkingItem(null);
    }
  };

  const getPersonStats = (personId) => {
    const pending = pendingItems.filter(item => item.related_person_id === personId);
    const discussed = discussedItems.filter(item => item.related_person_id === personId);
    return { pending: pending.length, discussed: discussed.length };
  };

  return (
    <div>
      <h1>👥 Personas</h1>
      <p style={{ color: '#666', marginBottom: '20px' }}>
        Lista de personas detectadas y sus items de memoria
      </p>

      {error && <div className="error">Error: {error}</div>}

      <div className="card">
        <h2>Lista de Personas</h2>
        {people.length === 0 ? (
          <div style={{ color: '#666' }}>No hay personas con items pendientes</div>
        ) : (
          <div>
            {people.map(person => {
              const stats = getPersonStats(person.id);
              return (
                <div
                  key={person.id}
                  onClick={() => setSelectedPerson(person)}
                  style={{
                    padding: '15px',
                    margin: '5px 0',
                    background: selectedPerson?.id === person.id ? '#e7f3ff' : '#f8f9fa',
                    border: '1px solid #ddd',
                    borderRadius: '4px',
                    cursor: 'pointer',
                  }}
                >
                  <div style={{ fontWeight: 'bold', marginBottom: '5px' }}>
                    {person.name}
                  </div>
                  <div style={{ fontSize: '12px', color: '#666' }}>
                    Pendientes: {stats.pending} | Discutidos: {stats.discussed}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {selectedPerson && (
        <div>
          <div className="card">
            <h2>Persona: {selectedPerson.name}</h2>
            <div style={{ marginBottom: '10px', fontSize: '14px', color: '#666' }}>
              <strong>ID:</strong> {selectedPerson.id}
            </div>
          </div>

          <div className="card">
            <h3>Items Pendientes ({pendingItems.length})</h3>
            {loading ? (
              <div>Cargando...</div>
            ) : (
              <div>
                {pendingItems.map(item => (
                  <div key={item.id} className="item pending" style={{ marginBottom: '10px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                      <div style={{ flex: 1 }}>
                        <strong>{item.content}</strong>
                        <div style={{ fontSize: '12px', color: '#666', marginTop: '5px' }}>
                          Tipo: {item.type} | Creado: {new Date(item.created_at).toLocaleString('es-ES')}
                        </div>
                      </div>
                      <button
                        onClick={() => handleMarkAsDiscussed(item.id)}
                        disabled={markingItem === item.id}
                        style={{
                          background: '#28a745',
                          fontSize: '12px',
                          padding: '5px 10px',
                          marginLeft: '10px',
                        }}
                      >
                        {markingItem === item.id ? 'Marcando...' : 'Marcar discutido (Debug)'}
                      </button>
                    </div>
                  </div>
                ))}
                {pendingItems.length === 0 && (
                  <div style={{ color: '#666' }}>No hay items pendientes</div>
                )}
              </div>
            )}
          </div>

          <div className="card">
            <h3>Items Discutidos (últimos 20)</h3>
            {loading ? (
              <div>Cargando...</div>
            ) : (
              <div>
                {discussedItems.map(item => (
                  <div key={item.id} className="item discussed" style={{ marginBottom: '10px' }}>
                    <strong>{item.content}</strong>
                    <div style={{ fontSize: '12px', color: '#666', marginTop: '5px' }}>
                      Tipo: {item.type} | Creado: {new Date(item.created_at).toLocaleString('es-ES')}
                    </div>
                  </div>
                ))}
                {discussedItems.length === 0 && (
                  <div style={{ color: '#666' }}>No hay items discutidos</div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
