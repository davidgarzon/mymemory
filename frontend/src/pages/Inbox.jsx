import React, { useState } from 'react';
import { sendInbox } from '../api';
import JsonBox from '../components/JsonBox';
import WarningBox from '../components/WarningBox';

export default function Inbox() {
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState(null);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!text.trim()) return;

    setLoading(true);
    setError(null);
    setResponse(null);

    try {
      const result = await sendInbox(text);
      setResponse(result);
      setText('');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const renderInterpretation = () => {
    if (!response) return null;

    const { intent, memory_item, detail, created, pending_items } = response;

    return (
      <div>
        {/* 1. Intent detectado */}
        <div className="card">
          <h3>1. Intent Detectado</h3>
          <div style={{ fontSize: '18px', fontWeight: 'bold', color: intent === 'unknown' ? '#dc3545' : '#28a745' }}>
            {intent}
          </div>
          {detail && (
            <div style={{ marginTop: '10px', color: '#666' }}>
              {detail}
            </div>
          )}
        </div>

        {/* 2. Persona */}
        {memory_item && memory_item.related_person_name && (
          <div className="card">
            <h3>2. Persona</h3>
            <div style={{ marginBottom: '10px' }}>
              <strong>Nombre detectado:</strong> {memory_item.related_person_name || '(no disponible)'}
            </div>
            <div style={{ marginBottom: '10px' }}>
              <strong>Person ID:</strong> {memory_item.related_person_id || '(no disponible)'}
            </div>
            <div style={{ fontSize: '12px', color: '#666' }}>
              <em>Nota: El backend normaliza nombres y gestiona aliases internamente</em>
            </div>
          </div>
        )}

        {/* 3. Contenido */}
        {memory_item && (
          <div className="card">
            <h3>3. Contenido</h3>
            <div style={{ marginBottom: '10px' }}>
              <strong>Contenido raw:</strong>
              <div style={{ 
                background: '#f8f9fa', 
                padding: '10px', 
                borderRadius: '4px', 
                marginTop: '5px',
                fontStyle: 'italic'
              }}>
                {memory_item.content || '(no disponible)'}
              </div>
            </div>
            <div style={{ marginBottom: '10px' }}>
              <strong>Fingerprint:</strong>
              <div style={{ 
                background: '#f8f9fa', 
                padding: '10px', 
                borderRadius: '4px', 
                marginTop: '5px',
                fontSize: '11px',
                fontFamily: 'monospace',
                wordBreak: 'break-all'
              }}>
                {memory_item.content_fingerprint || '(no disponible en respuesta del backend)'}
              </div>
            </div>
            <div style={{ marginBottom: '10px' }}>
              <strong>Normalized Summary:</strong>
              <div style={{ 
                background: '#f8f9fa', 
                padding: '10px', 
                borderRadius: '4px', 
                marginTop: '5px',
                fontSize: '12px',
                fontStyle: 'italic'
              }}>
                {memory_item.normalized_summary || '(no disponible en respuesta del backend)'}
              </div>
            </div>
            <div style={{ fontSize: '12px', color: '#666' }}>
              <em>El backend normaliza el contenido y calcula un fingerprint para deduplicación</em>
            </div>
          </div>
        )}

        {/* 4. Resultado */}
        <div className="card">
          <h3>4. Resultado</h3>
          <div style={{ marginBottom: '10px' }}>
            <strong>Creado:</strong>{' '}
            <span style={{ 
              color: created ? '#28a745' : '#ffc107',
              fontWeight: 'bold'
            }}>
              {created ? 'SÍ' : 'NO'}
            </span>
          </div>
          {!created && detail && (
            <div style={{ marginBottom: '10px', color: '#856404' }}>
              <strong>Motivo:</strong> {detail}
            </div>
          )}
          {memory_item && (
            <div style={{ marginBottom: '10px' }}>
              <strong>Memory Item ID:</strong> {memory_item.id}
            </div>
          )}
          {detail && created && (
            <div style={{ color: '#28a745', marginTop: '10px' }}>
              ✅ {detail}
            </div>
          )}
        </div>

        {/* 5. Lista pendientes (si es list_pending intent) */}
        {intent === 'list_pending' && pending_items && (
          <div className="card">
            <h3>Items Pendientes</h3>
            {pending_items.length === 0 ? (
              <div style={{ color: '#666' }}>No hay items pendientes</div>
            ) : (
              <div>
                {pending_items.map(item => (
                  <div key={item.id} className="item pending" style={{ marginBottom: '10px' }}>
                    <strong>{item.content}</strong>
                    <div style={{ fontSize: '12px', color: '#666', marginTop: '5px' }}>
                      Persona: {item.related_person_name || 'Sin persona'} | 
                      Tipo: {item.type} | 
                      Creado: {new Date(item.created_at).toLocaleString('es-ES')}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* 6. JSON crudo */}
        <JsonBox data={response} title="5. JSON Crudo (Respuesta Completa del Backend)" />
      </div>
    );
  };

  return (
    <div>
      <h2>Inbox — "¿He entendido al humano?"</h2>
      
      <div className="card">
        <form onSubmit={handleSubmit}>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder='Ej: "Recuérdame hablar con Toni de salarios" o "Qué tengo pendiente"'
            disabled={loading}
            style={{ minHeight: '120px' }}
          />
          <button type="submit" disabled={loading || !text.trim()}>
            {loading ? 'Enviando...' : 'Enviar'}
          </button>
        </form>
      </div>

      {error && <div className="error">Error: {error}</div>}
      
      {response && renderInterpretation()}
    </div>
  );
}
