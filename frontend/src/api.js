import axios from 'axios'

const API = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000'
})

const TOKEN_KEY = 'svp_token'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY)
}

API.interceptors.request.use((config) => {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

API.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      clearToken()
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export const register = (username, password) =>
  API.post('/api/auth/register', { username, password })

export const login = (username, password) =>
  API.post('/api/auth/login', { username, password })

export const getMe = () => API.get('/api/me')

export const regenerateKey = () => API.post('/api/auth/regenerate-key')

export const getServers = () => API.get('/api/servers')

export const getReport = (serverId) => API.get(`/api/report/${serverId}`)

export async function downloadPdfReport(serverId, hostname) {
  const res = await API.get(`/api/report/${serverId}/pdf`, { responseType: 'blob' })
  const url = window.URL.createObjectURL(new Blob([res.data]))
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', `security-report-${hostname}.pdf`)
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}

export default API
