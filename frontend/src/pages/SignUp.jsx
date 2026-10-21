import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || ''

export default function SignUp() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [done, setDone] = useState(false)
  const { signup, googleAuth } = useAuth()

  useEffect(() => {
    if (!GOOGLE_CLIENT_ID || done) return
    const script = document.createElement('script')
    script.src = 'https://accounts.google.com/gsi/client'
    script.async = true
    script.defer = true
    script.onload = () => {
      window.google?.accounts.id.initialize({
        client_id: GOOGLE_CLIENT_ID,
        callback: async ({ credential }) => {
          setError('')
          setLoading(true)
          try {
            await googleAuth(credential)
          } catch (e) {
            setError(e.response?.data?.error || 'Google sign-in failed')
          } finally {
            setLoading(false)
          }
        },
      })
      window.google?.accounts.id.renderButton(
        document.getElementById('google-signup-btn'),
        { theme: 'outline', size: 'large', width: 400, text: 'signup_with' }
      )
    }
    document.head.appendChild(script)
    return () => document.head.removeChild(script)
  }, [done]) // eslint-disable-line

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (password !== confirmPassword) { setError('Passwords do not match'); return }
    setLoading(true); setError('')
    try {
      await signup(email, password)
      setDone(true)
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to create account')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-background dark:bg-gray-900 min-h-screen flex flex-col justify-center items-center text-on-surface dark:text-gray-100 antialiased">
      <main className="w-full flex justify-center items-center">
        <div className="flex flex-col w-full items-center justify-center py-10 px-4 relative overflow-hidden">
          <div className="absolute -top-40 left-1/2 -translate-x-1/2 w-[720px] h-[480px] bg-gradient-to-b from-primary-container/20 via-secondary-container/10 to-transparent blur-3xl pointer-events-none rounded-full" />
          <div className="absolute top-1/3 -left-32 w-80 h-80 bg-tertiary-container/15 blur-3xl pointer-events-none rounded-full" />
          <div className="absolute bottom-10 -right-24 w-96 h-96 bg-secondary-container/20 blur-3xl pointer-events-none rounded-full" />

          <div className="relative w-full max-w-[480px] z-10">
            <div className="bg-surface-container/90 backdrop-blur-xl rounded-3xl p-8 shadow-xl flex flex-col">

              {done ? (
                <div className="flex flex-col items-center text-center gap-4 py-4">
                  <div className="w-14 h-14 rounded-full bg-tertiary/20 flex items-center justify-center">
                    <svg className="w-7 h-7 text-tertiary" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                  </div>
                  <h2 className="text-xl font-semibold">Check your inbox</h2>
                  <p className="text-on-surface-variant text-sm leading-relaxed">
                    We sent a verification link to <strong>{email}</strong>.
                    Click it to activate your account.
                  </p>
                  <p className="text-xs text-outline mt-2">
                    Didn't receive it?{' '}
                    <Link to="/signin" className="text-tertiary hover:underline">Go to sign in to resend</Link>
                  </p>
                </div>
              ) : (
                <>
                  <div className="flex flex-col items-center text-center">
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-primary-container to-secondary flex items-center justify-center shadow-lg mb-4">
                      <svg className="w-6 h-6 text-on-primary" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" viewBox="0 0 24 24">
                        <path d="M12 2L2 7l10 5 10-5-10-5z" /><path d="M2 17l10 5 10-5" /><path d="M2 12l10 5 10-5" />
                      </svg>
                    </div>
                    <h1 className="text-xl font-semibold">Create your account</h1>
                    <p className="text-sm text-on-surface-variant mt-1.5">Sign up and verify your email to get started</p>
                  </div>

                  {error && (
                    <div className="mt-6 p-3 bg-error/10 border border-error/20 rounded-lg">
                      <p className="text-sm text-error">{error}</p>
                    </div>
                  )}

                  <form className="flex flex-col gap-4 mt-6" onSubmit={handleSubmit}>
                    <div className="flex flex-col gap-1.5">
                      <label className="text-sm text-on-surface-variant font-medium" htmlFor="email">Email</label>
                      <input className="w-full bg-surface-container-lowest text-on-surface placeholder:text-outline-variant px-3.5 py-2.5 rounded-lg focus:bg-surface-container-low focus:outline-none"
                        id="email" type="email" placeholder="you@example.com"
                        value={email} onChange={e => setEmail(e.target.value)} required />
                    </div>

                    <div className="flex flex-col gap-1.5">
                      <label className="text-sm text-on-surface-variant font-medium" htmlFor="password">Password</label>
                      <div className="relative flex items-center">
                        <input className="w-full bg-surface-container-lowest text-on-surface placeholder:text-outline-variant px-3.5 py-2.5 pr-10 rounded-lg focus:bg-surface-container-low focus:outline-none"
                          id="password" type={showPassword ? 'text' : 'password'} placeholder="••••••••••••"
                          value={password} onChange={e => setPassword(e.target.value)} required />
                        <button type="button" className="absolute right-3 text-outline hover:text-on-surface" onClick={() => setShowPassword(v => !v)}>
                          <span className="material-symbols-outlined text-lg">{showPassword ? 'visibility_off' : 'visibility'}</span>
                        </button>
                      </div>
                    </div>

                    <div className="flex flex-col gap-1.5">
                      <label className="text-sm text-on-surface-variant font-medium" htmlFor="confirmPassword">Confirm Password</label>
                      <input className="w-full bg-surface-container-lowest text-on-surface placeholder:text-outline-variant px-3.5 py-2.5 rounded-lg focus:bg-surface-container-low focus:outline-none"
                        id="confirmPassword" type={showPassword ? 'text' : 'password'} placeholder="••••••••••••"
                        value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} required />
                    </div>

                    <button type="submit" disabled={loading}
                      className="w-full mt-3 py-2.5 px-4 rounded-lg bg-primary hover:bg-primary-fixed text-on-primary font-semibold disabled:opacity-50 disabled:cursor-not-allowed">
                      {loading ? 'Creating account...' : 'Create Account'}
                    </button>
                  </form>

                  <div className="mt-6 text-center">
                    <p className="text-sm text-on-surface-variant">
                      Already have an account?{' '}
                      <Link to="/signin" className="text-tertiary hover:text-tertiary-fixed font-medium">Sign in</Link>
                    </p>
                  </div>

                  {GOOGLE_CLIENT_ID && (
                    <>
                      <div className="flex items-center gap-3 my-4">
                        <div className="flex-1 h-px bg-outline-variant/40" />
                        <span className="text-xs text-on-surface-variant">or</span>
                        <div className="flex-1 h-px bg-outline-variant/40" />
                      </div>
                      <div id="google-signup-btn" className="flex justify-center" />
                    </>
                  )}
                </>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
