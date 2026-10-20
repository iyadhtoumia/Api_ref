import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000'

axios.defaults.baseURL = API_URL
axios.defaults.timeout = 0

const token = localStorage.getItem('token')
if (token) {
  axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
}

// Auto sign-out on expired/invalid token
axios.interceptors.response.use(
  res => res,
  err => {
    if (err.response?.status === 401) {
      const msg = err.response?.data?.error || ''
      if (msg === 'Token has expired' || msg === 'Invalid token') {
        localStorage.removeItem('token')
        delete axios.defaults.headers.common['Authorization']
        window.location.href = '/signin'
      }
    }
    return Promise.reject(err)
  }
)

export default axios
