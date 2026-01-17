import React, { useState, useEffect } from 'react';
import { listOutbox } from '../api';
import WarningBox from '../components/WarningBox';
import JsonBox from '../components/JsonBox';
import List from '../components/List';

export default function Outbox() {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [endpointAvailable, setEndpointAvailable] = useState(true);

  useEffect(() => {
    loadOutbox();
  }, []);

  const loadOutbox = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listOutbox();
      setNotifications(data);
      setEndpointAvailable(true);
    } catch (err) {
      setEndpointAvailable(false);
      setError(err.message);
      setNotifications([]);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      scheduled: '#17a2b8',
      sent: '#28a745',
      cancelled: '#dc3545',
      skipped: '#ffc107',
    };
    return colors[status] || '#6c757d';
  };

  if (!endpointAvailable) {
    return (
      <div>
        <h2>Outbox / Observabilidad — "¿Qué iba a hacer el sistema?"</h2>
        <WarningBox 
          message="⚠️ Outbox no implementado aún en el backend. Este endpoint no está disponible."
          type="error"
        />
        <div className="card">
          <p style={{ color: '#666' }}>
            Cuando el backend implemente el endpoint <code>GET /api/v1/outbox</code>, 
            aquí se mostrarán las notificaciones que el sistema habría enviado.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div>
      <h2>Outbox / Observabilidad — "¿Qué iba a hacer el sistema?"</h2>

      {error && <div className="error">Error: {error}</div>}

      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3>Notificaciones</h3>
          <button onClick={loadOutbox} disabled={loading}>
            {loading ? 'Cargando...' : '🔄 Refrescar'}
          </button>
        </div>
      </div>

      {notifications.length === 0 && !loading && (
        <WarningBox 
          message="No hay notificaciones en el outbox."
          type="info"
        />
      )}

      <div className="card">
        <List
          items={notifications}
          renderItem={(notification) => (
            <div style={{
              padding: '15px',
              margin: '5px 0',
              border: '1px solid #ddd',
              borderRadius: '4px',
              background: '#f8f9fa',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
                <div>
                  <strong>Canal:</strong> {notification.channel}
                </div>
                <div style={{
                  color: getStatusColor(notification.status),
                  fontWeight: 'bold',
                }}>
                  {notification.status}
                </div>
              </div>
              
              <div style={{ marginBottom: '5px' }}>
                <strong>Programado para:</strong> {new Date(notification.scheduled_for).toLocaleString('es-ES')}
              </div>
              
              {notification.sent_at && (
                <div style={{ marginBottom: '5px', color: '#28a745' }}>
                  <strong>Enviado:</strong> {new Date(notification.sent_at).toLocaleString('es-ES')}
                </div>
              )}
              
              <div style={{ marginBottom: '5px' }}>
                <strong>Evento ID:</strong> {notification.calendar_event_id}
              </div>
              
              <div style={{ marginBottom: '5px' }}>
                <strong>Persona ID:</strong> {notification.person_id}
              </div>
              
              {notification.briefing_text && (
                <div style={{ marginBottom: '5px' }}>
                  <strong>Briefing:</strong>
                  <div style={{
                    background: '#f8f9fa',
                    padding: '10px',
                    borderRadius: '4px',
                    marginTop: '5px',
                    fontSize: '12px',
                  }}>
                    {notification.briefing_text}
                  </div>
                </div>
              )}
              
              {notification.push_text && (
                <div style={{ marginBottom: '5px' }}>
                  <strong>Push Text:</strong>
                  <div style={{
                    background: '#f8f9fa',
                    padding: '10px',
                    borderRadius: '4px',
                    marginTop: '5px',
                    fontSize: '12px',
                  }}>
                    {notification.push_text}
                  </div>
                </div>
              )}
              
              {notification.error && (
                <div style={{ marginTop: '10px', color: '#dc3545' }}>
                  <strong>Error:</strong> {notification.error}
                </div>
              )}
              
              <div style={{ fontSize: '11px', color: '#999', marginTop: '10px' }}>
                Creado: {new Date(notification.created_at).toLocaleString('es-ES')}
              </div>
            </div>
          )}
          emptyMessage="No hay notificaciones"
        />
      </div>

      {notifications.length > 0 && (
        <JsonBox data={notifications} title="Outbox (JSON)" />
      )}
    </div>
  );
}
