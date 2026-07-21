import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export const health = () => api.get('/health')
export const listProjects = () => api.get('/projects')
export const createProject = (data) => api.post('/projects', null, { params: data })
export const getProject = (id) => api.get(`/projects/${id}`)
export const listScans = () => api.get('/scans')
export const createScan = (params) => api.post('/scans', null, { params })
export const getScan = (id) => api.get(`/scans/${id}`)
export const runScan = (id, data) => api.post(`/scans/${id}/run`, data)
export const getScanVulnerabilities = (scanId) => api.get(`/reports/scan/${scanId}`)
export const agentStatus = () => api.get('/agents/status')
export const analyzeCode = (data) => api.post('/agents/analyze', data)
