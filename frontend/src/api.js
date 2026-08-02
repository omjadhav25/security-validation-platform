import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const API = axios.create({
  baseURL: BASE_URL
})

export const getServers = () => API.get('/api/servers')
export const getReport = (serverId) => API.get(`/api/report/${serverId}`)