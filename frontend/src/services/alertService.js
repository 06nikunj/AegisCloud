import api from './api'

export const listAlerts = () => api.get('/alerts').then((r) => r.data)
export const acknowledgeAlert = (id) => api.put(`/alerts/${id}/acknowledge`).then((r) => r.data)