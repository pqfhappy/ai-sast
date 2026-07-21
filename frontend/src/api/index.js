import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export const health = () => api.get('/health')
export const listProjects = () => api.get('/projects')
export const createProject = (data) => api.post('/projects', data)
export const getProject = (id) => api.get(`/projects/${id}`)
export const listScans = () => api.get('/scans')
export const createScan = (data) => api.post('/scans', data)
export const getScanVulnerabilities = (scanId) => api.get(`/reports/scan/${scanId}`)
export const agentStatus = () => api.get('/agents/status')
