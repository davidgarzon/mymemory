import React, { useState } from 'react';

const API_BASE = 'http://localhost:8000/api/v1';

async function testEndpoint(endpoint, method = 'GET', body = null) {
  try {
    const options = {
      method,
      headers: { 'Content-Type': 'application/json' },
    };
    if (body) {
      options.body = JSON.stringify(body);
    }
    const response = await fetch(`${API_BASE}${endpoint}`, options);
    const data = await response.json();
    return { ok: response.ok, status: response.status, data };
  } catch (err) {
    return { ok: false, error: err.message };
  }
}

export default function Debug() {
  const [showRaw, setShowRaw] = useState(true);
  const [logs, setLogs] = useState([]);
  const [testEndpointInput, setTestEndpointInput] = useState('/health');
  const [testMethod, setTestMethod] = useState('GET');
  const [testBody, setTestBody] = useState('');

  const addLog = (message, type = 'info') => {
    const log = {
      id: Date.now(),
      timestamp: new Date().toLocaleTimeString('es-ES'),
      message,
      type,
    };
    setLogs(prev => [log, ...prev]);
  };

  const handleTestEndpoint = async () => {
    addLog(`Testing ${testMethod} ${testEndpointInput}`, 'info');
    
    let body = null;
    if (testBody.trim()) {
      try {
        body = JSON.parse(testBody);
      } catch (e) {
        addLog(`Error parsing JSON: ${e.message}`, 'error');
        return;
      }
    }

    const result = await testEndpoint(testEndpointInput, testMethod, body);
    
    if (result.ok) {
      addLog(`✅ ${testMethod} ${testEndpointInput} → ${result.status}`, 'success');
      addLog(`Response: ${JSON.stringify(result.data, null, 2)}`, 'data');
    } else {
      addLog(`❌ ${testMethod} ${testEndpointInput} → ${result.status || 'Error'}`, 'error');
      if (result.data) {
        addLog(`Error: ${JSON.stringify(result.data, null, 2)}`, 'error');
      }
      if (result.error) {
        addLog(`Exception: ${result.error}`, 'error');
      }
    }
  };

  const clearLogs = () => {
    setLogs([]);
  };

  return (
    <div>
      <h1>🐛 Debug</h1>
      <p style={{ color: '#666', marginBottom: '20px' }}>
        Panel de debugging y testing de endpoints
      </p>

      <div className="card">
        <h2>Configuración</h2>
        <div style={{ marginBottom: '15px', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={showRaw}
              onChange={(e) => setShowRaw(e.target.checked)}
            />
            <span>Mostrar JSON Raw / Resumen</span>
          </label>
        </div>
      </div>

      <div className="card">
        <h2>Test Endpoint Manual</h2>
        <div style={{ display: 'flex', gap: '10px', marginBottom: '10px', alignItems: 'center' }}>
          <select
            value={testMethod}
            onChange={(e) => setTestMethod(e.target.value)}
            style={{ width: '100px' }}
          >
            <option value="GET">GET</option>
            <option value="POST">POST</option>
            <option value="PUT">PUT</option>
            <option value="DELETE">DELETE</option>
          </select>
          <input
            type="text"
            value={testEndpointInput}
            onChange={(e) => setTestEndpointInput(e.target.value)}
            placeholder="/health"
            style={{ flex: 1 }}
          />
          <button onClick={handleTestEndpoint}>Test</button>
        </div>
        {testMethod === 'POST' || testMethod === 'PUT' ? (
          <textarea
            value={testBody}
            onChange={(e) => setTestBody(e.target.value)}
            placeholder='{"key": "value"}'
            style={{ minHeight: '80px', fontFamily: 'monospace', fontSize: '12px' }}
          />
        ) : null}
      </div>

      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
          <h2>Logs de Debug</h2>
          <button onClick={clearLogs} style={{ background: '#dc3545' }}>
            Limpiar Logs
          </button>
        </div>
        <div style={{
          maxHeight: '600px',
          overflowY: 'auto',
          background: '#1e1e1e',
          color: '#d4d4d4',
          padding: '15px',
          borderRadius: '4px',
          fontFamily: 'monospace',
          fontSize: '12px',
        }}>
          {logs.length === 0 ? (
            <div style={{ color: '#666' }}>No hay logs aún. Prueba un endpoint.</div>
          ) : (
            logs.map(log => (
              <div
                key={log.id}
                style={{
                  marginBottom: '10px',
                  padding: '8px',
                  background: log.type === 'error' ? '#3a1f1f' : log.type === 'success' ? '#1f3a1f' : '#1f1f3a',
                  borderRadius: '4px',
                }}
              >
                <div style={{ color: '#888', fontSize: '11px', marginBottom: '5px' }}>
                  [{log.timestamp}] {log.type.toUpperCase()}
                </div>
                <div style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                  {log.message}
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      <div className="card">
        <h2>Endpoints Disponibles</h2>
        <div style={{ fontFamily: 'monospace', fontSize: '13px' }}>
          <div style={{ marginBottom: '10px' }}>
            <strong>POST</strong> /api/v1/inbox
          </div>
          <div style={{ marginBottom: '10px' }}>
            <strong>GET</strong> /api/v1/memory/pending
          </div>
          <div style={{ marginBottom: '10px' }}>
            <strong>GET</strong> /api/v1/calendar/events/{'{id}'}/briefing
          </div>
          <div style={{ marginBottom: '10px' }}>
            <strong>POST</strong> /api/v1/calendar/events
          </div>
          <div style={{ marginBottom: '10px' }}>
            <strong>POST</strong> /api/v1/calendar/events/{'{id}'}/close
          </div>
          <div style={{ marginBottom: '10px' }}>
            <strong>GET</strong> /health
          </div>
        </div>
      </div>
    </div>
  );
}
