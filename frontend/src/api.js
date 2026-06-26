import axios from 'axios'

const API = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000'
})

export const getServers = () => API.get('/api/servers')
export const getReport = (serverId) => API.get(`/api/report/${serverId}`)