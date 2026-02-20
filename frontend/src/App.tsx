import { Activity, Database, MessageSquare, Settings } from 'lucide-react';
import { useEffect, useState } from 'react';
import './App.css';
import type { Connector, HealthStatus } from './services/api';
import { apiService } from './services/api';
function App() {
  const [connectors, setConnectors] = useState<Connector[]>([]);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [selectedConnector, setSelectedConnector] = useState<string>('');
  const [question, setQuestion] = useState('');
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadConnectors();
    loadHealth();
    const interval = setInterval(loadHealth, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const loadConnectors = async () => {
    try {
      const data = await apiService.getConnectors();
      setConnectors(data.connectors || []);
      if (data.connectors?.length > 0 && !selectedConnector) {
        setSelectedConnector(data.connectors[0].id);
      }
    } catch (error) {
      console.error('Error loading connectors:', error);
    }
  };

  const loadHealth = async () => {
    try {
      const data = await apiService.getHealth();
      setHealth(data);
    } catch (error) {
      console.error('Error loading health:', error);
    }
  };

  const handleAsk = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || !selectedConnector) return;

    setLoading(true);
    setResult(null);

    try {
      const data = await apiService.askQuestion(selectedConnector, question);
      setResult(data);
    } catch (error: any) {
      setResult({
        success: false,
        error: error.response?.data?.detail || error.message,
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-content">
          <h1>
            <Database size={32} />
            OnePilot
          </h1>
          <div className="header-stats">
            {health && (
              <>
                <div className={`status-badge ${health.status}`}>
                  <Activity size={16} />
                  {health.status}
                </div>
                <span>{health.total_connectors} connecteurs</span>
                <span>{health.healthy} healthy</span>
              </>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="main-content">
        {/* Sidebar */}
        <aside className="sidebar">
          <div className="sidebar-section">
            <h3>
              <Settings size={18} />
              Connecteurs
            </h3>
            {connectors.length === 0 ? (
              <p className="no-connectors">Aucun connecteur</p>
            ) : (
              <div className="connector-list">
                {connectors.map((conn) => (
                  <button
                    key={conn.id}
                    className={`connector-item ${
                      selectedConnector === conn.id ? 'active' : ''
                    }`}
                    onClick={() => setSelectedConnector(conn.id)}
                  >
                    <Database size={16} />
                    <div className="connector-info">
                      <span className="connector-name">{conn.name}</span>
                      <span className="connector-type">{conn.type}</span>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </aside>

        {/* Chat Area */}
        <div className="chat-area">
          <div className="chat-header">
            <MessageSquare size={20} />
            <h2>Posez votre question</h2>
          </div>

          <div className="chat-body">
            {result && (
              <div className="result-container">
                {result.success ? (
                  <>
                    <div className="result-question">
                      <strong>Question:</strong> {result.question}
                    </div>
                    <div className="result-sql">
                      <strong>SQL généré:</strong>
                      <pre>{result.sql}</pre>
                    </div>
                    <div className="result-data">
                      <strong>
                        Résultats ({result.count} ligne
                        {result.count > 1 ? 's' : ''}) :
                      </strong>
                      {result.results.length > 0 ? (
                        <div className="table-container">
                          <table>
                            <thead>
                              <tr>
                                {Object.keys(result.results[0]).map((key) => (
                                  <th key={key}>{key}</th>
                                ))}
                              </tr>
                            </thead>
                            <tbody>
                              {result.results.map((row: any, idx: number) => (
                                <tr key={idx}>
                                  {Object.values(row).map((val: any, i) => (
                                    <td key={i}>{String(val)}</td>
                                  ))}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      ) : (
                        <p>Aucun résultat</p>
                      )}
                    </div>
                    <div className="result-meta">
                      <span>⚡ LLM: {result.llm_time_ms}ms</span>
                      <span>🔍 Query: {result.query_time_ms}ms</span>
                    </div>
                  </>
                ) : (
                  <div className="result-error">
                    <strong>Erreur:</strong> {result.error}
                  </div>
                )}
              </div>
            )}
          </div>

          <form className="chat-input" onSubmit={handleAsk}>
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Posez votre question en français..."
              disabled={loading || !selectedConnector}
            />
            <button type="submit" disabled={loading || !selectedConnector}>
              {loading ? 'En cours...' : 'Envoyer'}
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}

export default App;