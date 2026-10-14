import axios from 'axios'

// Configure axios defaults
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000'

axios.defaults.baseURL = API_URL

// NO TIMEOUT - same as Telegram bot
axios.defaults.timeout = 0

// Add token to requests automatically
const token = localStorage.getItem('token')
if (token) {
  axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
}

export default axios
