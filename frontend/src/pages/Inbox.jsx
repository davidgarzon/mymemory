import React, { useState } from 'react';
import { sendInbox } from '../api';
import JsonBox from '../components/JsonBox';

export default function Inbox() {
  const [text, setText] = useState('');
  const [useLLM, setUseLLM] = useState(true);
  const [loading, setLoading] = useState(false);
  const [logs, setLogs] = useState([]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!text.trim()) return;

    setLoading(true);
    const timestamp = new Date().toLocaleTimeString('es-ES');
    const logEntry = {
      id: Date.now(),
      timestamp,
      input: text,
      response: null,
      error: null,
    };

    try {
      const result = await sendInbox(text, useLLM);
      logEntry.response = result;
      setLogs(prev => [logEntry, ...prev]);
      setText('');
    } catch (err) {
      logEntry.error = err.message;
      setLogs(prev => [logEntry, ...prev]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1>📥 Inbox</h1>
      <p style={{ color: '#666', marginBottom: '20px' }}>
        Envía mensajes al sistema y observa cómo los interpreta
      </p>

      <div className="card">
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '15px', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={useLLM}
                onChange={(e) => setUseLLM(e.target.checked)}
                disabled={loading}
              />
              <span>Forzar LLM / Solo reglas</span>
            </label>
            <span style={{ fontSize: '12px', color: '#666' }}>
              {useLLM ? 'LLM habilitado' : 'Solo parser determinista'}
            </span>
          </div>

          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder='Ej: "Recuérdame hablar con Toni de salarios" o "Apunta arroz, leche y pan"'
            disabled={loading}
            style={{ minHeight: '120px', fontFamily: 'monospace', fontSize: '14px' }}
          />
          <button type="submit" disabled={loading || !text.trim()}>
            {loading ? 'Enviando...' : 'Enviar'}
          </button>
        </form>
      </div>

      {logs.length > 0 && (
        <div className="card">
          <h2>Log Cronológico</h2>
          <div style={{ maxHeight: '600px', overflowY: 'auto' }}>
            {logs.map(log => (
              <div
                key={log.id}
                style={{
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  padding: '15px',
                  marginBottom: '15px',
                  background: log.error ? '#fff5f5' : '#f9f9f9',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
                  <strong style={{ color: '#666' }}>{log.timestamp}</strong>
                  {log.error && <span style={{ color: '#dc3545' }}>❌ Error</span>}
                  {log.response && <span style={{ color: '#28a745' }}>✅ OK</span>}
                </div>

                <div style={{ marginBottom: '10px' }}>
                  <strong>Input:</strong>
                  <div style={{
                    background: '#fff',
                    padding: '8px',
                    borderRadius: '4px',
                    marginTop: '5px',
                    fontFamily: 'monospace',
                    fontSize: '13px',
                  }}>
                    {log.input}
                  </div>
                </div>

                {log.error && (
                  <div style={{ color: '#dc3545', marginTop: '10px' }}>
                    <strong>Error:</strong> {log.error}
                  </div>
                )}

                {log.response && (
                  <div>
                    <strong>Respuesta del Backend:</strong>
                    <JsonBox data={log.response} title={null} />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
