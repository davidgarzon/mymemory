import React, { useState, useEffect } from 'react';
import { listOutbox } from '../api';
import JsonBox from '../components/JsonBox';

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
        <h1>📤 Outbox</h1>
        <p style={{ color: '#666', marginBottom: '20px' }}>
          Notificaciones que el sistema enviaría
        </p>
        <div className="card">
          <div style={{ padding: '20px', textAlign: 'center', color: '#666' }}>
            <p style={{ fontSize: '18px', marginBottom: '10px' }}>⚠️ Outbox no implementado aún</p>
            <p>El endpoint <code>GET /api/v1/outbox</code> no está disponible en el backend.</p>
            <p style={{ marginTop: '10px', fontSize: '14px' }}>
              Cuando se implemente, aquí se mostrarán las notificaciones programadas.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div>
      <h1>📤 Outbox</h1>
      <p style={{ color: '#666', marginBottom: '20px' }}>
        Notificaciones que el sistema enviaría (simulado, no se envía nada real)
      </p>

      {error && <div className="error">Error: {error}</div>}

      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2>Notificaciones</h2>
          <button onClick={loadOutbox} disabled={loading}>
            {loading ? 'Cargando...' : '🔄 Refrescar'}
          </button>
        </div>
      </div>

      {notifications.length === 0 && !loading && (
        <div className="card">
          <div style={{ padding: '20px', textAlign: 'center', color: '#666' }}>
            No hay notificaciones en el outbox
          </div>
        </div>
      )}

      {notifications.map(notification => (
        <div key={notification.id} className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '15px' }}>
            <div>
              <strong>Canal:</strong> {notification.channel}
            </div>
            <div style={{
              color: getStatusColor(notification.status),
              fontWeight: 'bold',
              padding: '5px 10px',
              background: '#f8f9fa',
              borderRadius: '4px',
            }}>
              {notification.status}
            </div>
          </div>
          
          <div style={{ marginBottom: '10px', fontSize: '14px' }}>
            <strong>Programado para:</strong> {new Date(notification.scheduled_for).toLocaleString('es-ES')}
          </div>
          
          {notification.sent_at && (
            <div style={{ marginBottom: '10px', fontSize: '14px', color: '#28a745' }}>
              <strong>Enviado:</strong> {new Date(notification.sent_at).toLocaleString('es-ES')}
            </div>
          )}
          
          <div style={{ marginBottom: '10px', fontSize: '14px' }}>
            <strong>Evento ID:</strong> {notification.calendar_event_id}
          </div>
          
          {notification.briefing_text && (
            <div style={{ marginBottom: '10px' }}>
              <strong>Briefing:</strong>
              <div style={{
                background: '#f8f9fa',
                padding: '10px',
                borderRadius: '4px',
                marginTop: '5px',
                fontSize: '13px',
                whiteSpace: 'pre-wrap',
              }}>
                {notification.briefing_text}
              </div>
            </div>
          )}
          
          {notification.push_text && (
            <div style={{ marginBottom: '10px' }}>
              <strong>Push Text:</strong>
              <div style={{
                background: '#f8f9fa',
                padding: '10px',
                borderRadius: '4px',
                marginTop: '5px',
                fontSize: '13px',
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
          
          <div style={{ marginTop: '15px' }}>
            <JsonBox data={notification} title="Payload Completo (JSON)" />
          </div>
        </div>
      ))}
    </div>
  );
}
