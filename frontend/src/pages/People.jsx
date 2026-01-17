import React, { useState, useEffect } from 'react';
import { listPeople, listPending, listAllItems } from '../api';
import List from '../components/List';
import WarningBox from '../components/WarningBox';

export default function People() {
  const [people, setPeople] = useState([]);
  const [selectedPerson, setSelectedPerson] = useState(null);
  const [pendingItems, setPendingItems] = useState([]);
  const [discussedItems, setDiscussedItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

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
      // Load pending items
      const pending = await listPending(personId);
      setPendingItems(pending);

      // Load discussed items
      const allItems = await listAllItems('discussed');
      const discussed = allItems
        .filter(item => item.related_person_id === personId)
        .slice(0, 10); // Last 10 discussed
      setDiscussedItems(discussed);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getPersonStats = (personId) => {
    const pending = pendingItems.filter(item => item.related_person_id === personId);
    const discussed = discussedItems.filter(item => item.related_person_id === personId);
    return { pending: pending.length, discussed: discussed.length };
  };

  return (
    <div>
      <h2>Personas — "¿Recuerdo como una persona real?"</h2>

      {error && <div className="error">Error: {error}</div>}

      <div className="card">
        <h3>Lista de Personas</h3>
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
            <h3>Persona: {selectedPerson.name}</h3>
            <div style={{ marginBottom: '10px' }}>
              <strong>ID:</strong> {selectedPerson.id}
            </div>
            <div style={{ fontSize: '12px', color: '#666', marginBottom: '15px' }}>
              <em>Nota: Aliases y normalización gestionados por el backend</em>
            </div>
          </div>

          <div className="card">
            <h3>Items Pendientes ({pendingItems.length})</h3>
            {loading ? (
              <div>Cargando...</div>
            ) : (
              <List
                items={pendingItems}
                renderItem={(item) => (
                  <div className="item pending">
                    <strong>{item.content}</strong>
                    <div style={{ fontSize: '12px', color: '#666', marginTop: '5px' }}>
                      Tipo: {item.type} | 
                      Creado: {new Date(item.created_at).toLocaleString('es-ES')}
                    </div>
                    {item.content_fingerprint && (
                      <div style={{ fontSize: '10px', color: '#999', marginTop: '3px', fontFamily: 'monospace' }}>
                        Fingerprint: {item.content_fingerprint.substring(0, 20)}...
                      </div>
                    )}
                  </div>
                )}
                emptyMessage="No hay items pendientes para esta persona"
              />
            )}
          </div>

          <div className="card">
            <h3>Items Discutidos (últimos 10)</h3>
            {loading ? (
              <div>Cargando...</div>
            ) : (
              <List
                items={discussedItems}
                renderItem={(item) => (
                  <div className="item discussed">
                    <strong>{item.content}</strong>
                    <div style={{ fontSize: '12px', color: '#666', marginTop: '5px' }}>
                      Tipo: {item.type} | 
                      Creado: {new Date(item.created_at).toLocaleString('es-ES')}
                    </div>
                  </div>
                )}
                emptyMessage="No hay items discutidos para esta persona"
              />
            )}
          </div>
        </div>
      )}
    </div>
  );
}
