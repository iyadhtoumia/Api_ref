import React, { createContext, useContext, useState, useEffect } from 'react'
import axios from '../utils/axios'

const AuthContext = createContext()

export function useAuth() {
  return useContext(AuthContext)
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
      fetchUser()
    } else {
      setLoading(false)
    }
  }, [])

  const fetchUser = async () => {
    try {
      const response = await axios.get('/api/auth/me')
      setUser(response.data.user)
    } catch (error) {
      localStorage.removeItem('token')
      delete axios.defaults.headers.common['Authorization']
    } finally {
      setLoading(false)
    }
  }

  const signin = async (email, password) => {
    const response = await axios.post('/api/auth/signin', { email, password })
    // Step 1: credentials valid, OTP sent
    if (response.data.otp_required) {
      return { otpRequired: true, email: response.data.email }
    }
    // Fallback: direct login (should not happen with 2FA active)
    const { token, user } = response.data
    localStorage.setItem('token', token)
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
    setUser(user)
    return user
  }

  const verifyOtp = async (email, otp, useTotp = false) => {
    const response = await axios.post('/api/auth/signin/verify-otp', { email, otp, use_totp: useTotp })
    const { token, user } = response.data
    localStorage.setItem('token', token)
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
    setUser(user)
    return user
  }

  const googleAuth = async (credential) => {
    const response = await axios.post('/api/auth/google', { credential })
    const { token, user } = response.data
    localStorage.setItem('token', token)
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
    setUser(user)
    return user
  }

  const signup = async (email, password) => {
    const response = await axios.post('/api/auth/signup', { email, password })
    // No token returned — user must verify email first
    return response.data
  }

  const setUserFromToken = (token, userData) => {
    localStorage.setItem('token', token)
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
    setUser(userData)
  }

  const signout = () => {
    localStorage.removeItem('token')
    delete axios.defaults.headers.common['Authorization']
    setUser(null)
  }

  const value = {
    user,
    signin,
    verifyOtp,
    googleAuth,
    signup,
    signout,
    setUserFromToken,
    refreshUser: fetchUser
  }

  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  )
}
