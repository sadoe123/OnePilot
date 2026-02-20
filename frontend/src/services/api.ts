import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface Connector {
  id: string;
  name: string;
  type: string;
  status: string;
  created_at: string;
}

export interface Conversation {
  id: string;
  question: string;
  sql_query: string;
  created_at: string;
}

export interface HealthStatus {
  status: string;
  total_connectors: number;
  healthy: number;
  unhealthy: number;
  errors: number;
}

export const apiService = {
  // Connecteurs
  getConnectors: async () => {
    const response = await api.get('/connectors');
    return response.data;
  },

  createConnector: async (data: any) => {
    const response = await api.post('/connectors', data);
    return response.data;
  },

  getConnectorSchema: async (connectorId: string) => {
    const response = await api.get(`/connectors/${connectorId}/schema`);
    return response.data;
  },

  // Questions
  askQuestion: async (connectorId: string, question: string) => {
    const response = await api.post('/ask', {
      connector_id: connectorId,
      question,
    });
    return response.data;
  },

  // Historique
  getHistory: async (limit: number = 10) => {
    const response = await api.get(`/history?limit=${limit}`);
    return response.data;
  },

  // Monitoring
  getHealth: async () => {
    const response = await api.get('/monitoring/health');
    return response.data;
  },

  getMetrics: async () => {
    const response = await api.get('/monitoring/metrics');
    return response.data;
  },
};

export default api;