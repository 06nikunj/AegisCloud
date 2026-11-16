import api from './api'

export const scanImage = (image) => api.post('/scan/image', { image }).then((r) => r.data)
export const listScans = () => api.get('/scan/results').then((r) => r.data)
export const getScanVulnerabilities = (id) => api.get(`/scan/results/${id}/vulnerabilities`).then((r) => r.data)