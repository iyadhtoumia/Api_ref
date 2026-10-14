import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function SignIn() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const { signin } = useAuth()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    
    try {
      await signin(email, password)
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to sign in')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-background min-h-screen flex flex-col justify-center items-center text-on-surface antialiased">
      <main className="w-full flex justify-center items-center">
        <div className="flex flex-col w-full items-center justify-center py-10 px-4 relative overflow-hidden">
          <div className="absolute -top-40 left-1/2 -translate-x-1/2 w-[720px] h-[480px] bg-gradient-to-b from-primary-container/20 via-secondary-container/10 to-transparent blur-3xl pointer-events-none rounded-full"></div>
          <div className="absolute top-1/3 -left-32 w-80 h-80 bg-tertiary-container/15 blur-3xl pointer-events-none rounded-full"></div>
          <div className="absolute bottom-10 -right-24 w-96 h-96 bg-secondary-container/20 blur-3xl pointer-events-none rounded-full"></div>
          
          <div className="relative w-full max-w-[480px] flex flex-col gap-y-6 z-10">
            <div className="bg-surface-container/90 backdrop-blur-xl rounded-3xl p-8 shadow-xl flex flex-col">
              <div className="flex flex-col items-center text-center">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-primary-container to-secondary flex items-center justify-center shadow-lg mb-4">
                  <svg className="w-6 h-6 text-on-primary select-none" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" viewBox="0 0 24 24">
                    <path d="M12 2L2 7l10 5 10-5-10-5z"></path>
                    <path d="M2 17l10 5 10-5"></path>
                    <path d="M2 12l10 5 10-5"></path>
                  </svg>
                </div>
                <h1 className="text-xl font-semibold text-on-surface">Welcome back</h1>
                <p className="text-sm text-on-surface-variant mt-1.5">Sign in to access your config lookups</p>
              </div>

              {error && (
                <div className="mt-6 p-3 bg-error/10 border border-error/20 rounded-lg">
                  <p className="text-sm text-error">{error}</p>
                </div>
              )}

              <form className="flex flex-col gap-4 mt-6" onSubmit={handleSubmit}>
                <div className="flex flex-col gap-1.5">
                  <label className="text-sm text-on-surface-variant font-medium" htmlFor="email">
                    Email
                  </label>
                  <input
                    className="w-full bg-surface-container-lowest text-on-surface placeholder:text-outline-variant px-3.5 py-2.5 rounded-lg focus:bg-surface-container-low focus:outline-none"
                    id="email"
                    type="email"
                    placeholder="you@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                  />
                </div>

                <div className="flex flex-col gap-1.5">
                  <label className="text-sm text-on-surface-variant font-medium" htmlFor="password">
                    Password
                  </label>
                  <div className="relative flex items-center">
                    <input
                      className="w-full bg-surface-container-lowest text-on-surface placeholder:text-outline-variant px-3.5 py-2.5 pr-10 rounded-lg focus:bg-surface-container-low focus:outline-none"
                      id="password"
                      type={showPassword ? 'text' : 'password'}
                      placeholder="••••••••••••"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                    />
                    <button
                      type="button"
                      className="absolute right-3 text-outline hover:text-on-surface"
                      onClick={() => setShowPassword(!showPassword)}
                    >
                      <span className="material-symbols-outlined text-lg">
                        {showPassword ? 'visibility_off' : 'visibility'}
                      </span>
                    </button>
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full mt-3 py-2.5 px-4 rounded-lg bg-primary hover:bg-primary-fixed text-on-primary font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? 'Signing in...' : 'Sign In'}
                </button>
              </form>

              <div className="mt-6 text-center">
                <p className="text-sm text-on-surface-variant">
                  Don't have an account?{' '}
                  <Link to="/signup" className="text-tertiary hover:text-tertiary-fixed font-medium">
                    Create account & get 100 coins
                  </Link>
                </p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
