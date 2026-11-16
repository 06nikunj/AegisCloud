import api from './api'

/** Ask the AI engine to explain a vulnerability. Resolves to { what_it_is, attack_scenario, remediation[], model }. */
export const analyzeVulnerability = (payload) => api.post('/ai/analyze', payload).then((r) => r.data)

/** Whether the AI provider is configured on the backend. Resolves to { provider, model, configured }. */
export const getAiStatus = () => api.get('/ai/status').then((r) => r.data)
