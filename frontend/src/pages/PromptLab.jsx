import React, { useState, useEffect } from 'react';
import {
  listPromptBlocks,
  savePromptBlock,
  deletePromptBlock,
  resetPromptBlocks,
  getActivePrompt,
  testPrompt,
} from '../api';
import JsonBox from '../components/JsonBox';

export default function PromptLab() {
  const [blocks, setBlocks] = useState([]);
  const [selectedBlock, setSelectedBlock] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [testInput, setTestInput] = useState('');
  const [testResult, setTestResult] = useState(null);
  const [testing, setTesting] = useState(false);
  const [showPrompt, setShowPrompt] = useState(false);
  const [activePrompt, setActivePrompt] = useState(null);

  useEffect(() => {
    loadBlocks();
    loadActivePrompt();
  }, []);

  const loadBlocks = async () => {
    setLoading(true);
    setError(null);
    try {
      const blocksData = await listPromptBlocks();
      setBlocks(blocksData);
      if (blocksData.length > 0 && !selectedBlock) {
        setSelectedBlock(blocksData[0]);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadActivePrompt = async () => {
    try {
      const result = await getActivePrompt();
      setActivePrompt(result.prompt);
    } catch (err) {
      // Ignore errors
    }
  };

  const handleSelectBlock = (block) => {
    setSelectedBlock(block);
  };

  const handleSaveBlock = async () => {
    if (!selectedBlock) return;

    setLoading(true);
    setError(null);
    try {
      const saved = await savePromptBlock({
        id: selectedBlock.id,
        name: selectedBlock.name,
        content: selectedBlock.content,
        enabled: selectedBlock.enabled,
        order: selectedBlock.order,
      });
      
      // Update blocks list
      await loadBlocks();
      setSelectedBlock(saved);
      await loadActivePrompt();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveAndTest = async () => {
    await handleSaveBlock();
    if (testInput.trim()) {
      handleTestPrompt();
    }
  };

  const handleDeleteBlock = async (blockId) => {
    if (!confirm('¿Eliminar este bloque?')) return;

    setLoading(true);
    setError(null);
    try {
      await deletePromptBlock(blockId);
      await loadBlocks();
      if (selectedBlock?.id === blockId) {
        setSelectedBlock(null);
      }
      await loadActivePrompt();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = async () => {
    if (!confirm('¿Resetear todos los bloques al prompt por defecto? Esto sobrescribirá los bloques existentes.')) return;

    setLoading(true);
    setError(null);
    try {
      await resetPromptBlocks();
      await loadBlocks();
      await loadActivePrompt();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleEnabled = async () => {
    if (!selectedBlock) return;
    
    const updated = {
      ...selectedBlock,
      enabled: !selectedBlock.enabled,
    };
    setSelectedBlock(updated);
    
    // Auto-save
    setLoading(true);
    try {
      await savePromptBlock(updated);
      await loadBlocks();
      await loadActivePrompt();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleTestPrompt = async () => {
    if (!testInput.trim()) return;

    setTesting(true);
    setError(null);
    try {
      const result = await testPrompt(testInput);
      setTestResult(result);
      await loadActivePrompt(); // Refresh active prompt
    } catch (err) {
      setError(err.message);
      setTestResult(null);
    } finally {
      setTesting(false);
    }
  };

  const handleCreateBlock = () => {
    const newBlock = {
      id: null,
      name: `BLOCK_${blocks.length + 1}`,
      content: '',
      enabled: true,
      order: blocks.length + 1,
    };
    setBlocks([...blocks, newBlock]);
    setSelectedBlock(newBlock);
  };

  return (
    <div>
      <h1>🧪 Prompt Lab</h1>
      <p style={{ color: '#666', marginBottom: '20px' }}>
        Edita y prueba el prompt del LLM sin modificar código
      </p>

      {error && <div className="error">Error: {error}</div>}

      <div style={{ display: 'flex', gap: '20px' }}>
        {/* Sidebar: Lista de bloques */}
        <div style={{ width: '250px', minHeight: '600px' }}>
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
              <h3>Bloques</h3>
              <button
                onClick={handleCreateBlock}
                style={{ fontSize: '12px', padding: '5px 10px' }}
              >
                + Nuevo
              </button>
            </div>
            <button
              onClick={handleReset}
              style={{
                width: '100%',
                marginBottom: '10px',
                background: '#dc3545',
                fontSize: '12px',
              }}
            >
              Resetear a Default
            </button>
            {loading && blocks.length === 0 ? (
              <div>Cargando...</div>
            ) : (
              <div>
                {blocks.map(block => (
                  <div
                    key={block.id || 'new'}
                    onClick={() => handleSelectBlock(block)}
                    style={{
                      padding: '10px',
                      margin: '5px 0',
                      background: selectedBlock?.id === block.id ? '#e7f3ff' : '#f8f9fa',
                      border: '1px solid #ddd',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                    }}
                  >
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 'bold', fontSize: '13px' }}>{block.name}</div>
                      <div style={{ fontSize: '11px', color: '#666' }}>
                        Order: {block.order} | {block.enabled ? '✓' : '✗'}
                      </div>
                    </div>
                    {block.id && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteBlock(block.id);
                        }}
                        style={{
                          background: '#dc3545',
                          fontSize: '11px',
                          padding: '3px 8px',
                        }}
                      >
                        ×
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Main: Editor del bloque */}
        <div style={{ flex: 1 }}>
          {selectedBlock ? (
            <div className="card">
              <h3>Editar Bloque: {selectedBlock.name}</h3>
              
              <div style={{ marginBottom: '15px', display: 'flex', gap: '15px', alignItems: 'center' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={selectedBlock.enabled}
                    onChange={handleToggleEnabled}
                  />
                  <span>Habilitado</span>
                </label>
                
                <div>
                  <label>Order:</label>
                  <input
                    type="number"
                    value={selectedBlock.order}
                    onChange={(e) => setSelectedBlock({
                      ...selectedBlock,
                      order: parseInt(e.target.value) || 0,
                    })}
                    style={{ width: '80px', marginLeft: '8px' }}
                  />
                </div>
              </div>

              <textarea
                value={selectedBlock.content}
                onChange={(e) => setSelectedBlock({
                  ...selectedBlock,
                  content: e.target.value,
                })}
                placeholder="Contenido del bloque..."
                disabled={loading}
                style={{
                  minHeight: '300px',
                  fontFamily: 'monospace',
                  fontSize: '13px',
                  width: '100%',
                }}
              />

              <div style={{ marginTop: '15px', display: 'flex', gap: '10px' }}>
                <button
                  onClick={handleSaveBlock}
                  disabled={loading}
                >
                  {loading ? 'Guardando...' : 'Guardar'}
                </button>
                <button
                  onClick={handleSaveAndTest}
                  disabled={loading || !testInput.trim()}
                  style={{ background: '#28a745' }}
                >
                  Guardar y Probar
                </button>
              </div>
            </div>
          ) : (
            <div className="card">
              <p style={{ color: '#666' }}>Selecciona un bloque o crea uno nuevo</p>
            </div>
          )}

          {/* Zona de test */}
          <div className="card" style={{ marginTop: '20px' }}>
            <h3>Zona de Test</h3>
            
            <div style={{ marginBottom: '15px' }}>
              <label>
                <strong>Prompt Activo:</strong>
                <button
                  onClick={() => setShowPrompt(!showPrompt)}
                  style={{
                    marginLeft: '10px',
                    fontSize: '12px',
                    padding: '5px 10px',
                  }}
                >
                  {showPrompt ? 'Ocultar' : 'Mostrar'}
                </button>
              </label>
              {showPrompt && activePrompt && (
                <div style={{
                  marginTop: '10px',
                  padding: '15px',
                  background: '#f8f9fa',
                  borderRadius: '4px',
                  fontFamily: 'monospace',
                  fontSize: '12px',
                  whiteSpace: 'pre-wrap',
                  maxHeight: '200px',
                  overflowY: 'auto',
                }}>
                  {activePrompt}
                </div>
              )}
            </div>

            <div style={{ marginBottom: '15px' }}>
              <label>
                <strong>Input de Prueba:</strong>
              </label>
              <textarea
                value={testInput}
                onChange={(e) => setTestInput(e.target.value)}
                placeholder='Ej: "añade arroz y manzanas" o "recuerdame hablar con toni de salarios"'
                disabled={testing}
                style={{
                  minHeight: '80px',
                  fontFamily: 'monospace',
                  fontSize: '13px',
                  marginTop: '8px',
                }}
              />
            </div>

            <button
              onClick={handleTestPrompt}
              disabled={testing || !testInput.trim()}
              style={{ background: '#17a2b8' }}
            >
              {testing ? 'Probando...' : 'Probar'}
            </button>

            {testResult && (
              <div style={{ marginTop: '20px' }}>
                <h4>Resultado del Test</h4>
                <div style={{ marginBottom: '10px', fontSize: '14px', color: '#666' }}>
                  <strong>Tiempo de respuesta:</strong> {testResult.response_time_ms}ms
                </div>
                <div>
                  <strong>Respuesta del LLM:</strong>
                  <JsonBox data={testResult.response} title={null} />
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
