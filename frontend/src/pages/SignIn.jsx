import React, { useState, useRef, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import axios from '../utils/axios'

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || ''

export default function SignIn() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [unverified, setUnverified] = useState(false)
  const [resendLoading, setResendLoading] = useState(false)
  const [resendDone, setResendDone] = useState(false)

  // 2FA step
  const [otpStep, setOtpStep] = useState(false)
  const [otpEmail, setOtpEmail] = useState('')
  const [otp, setOtp] = useState(['', '', '', '', '', ''])
  const [useAuthApp, setUseAuthApp] = useState(false)
  const otpRefs = useRef([])

  const { signin, verifyOtp, googleAuth } = useAuth()

  // Load Google GSI script and init button
  useEffect(() => {
    if (!GOOGLE_CLIENT_ID) return
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
        document.getElementById('google-signin-btn'),
        { theme: 'outline', size: 'large', width: 400, text: 'signin_with' }
      )
    }
    document.head.appendChild(script)
    return () => document.head.removeChild(script)
  }, []) // eslint-disable-line

  useEffect(() => {
    if (otpStep && otpRefs.current[0]) {
      otpRefs.current[0].focus()
    }
  }, [otpStep])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true); setError(''); setUnverified(false)
    try {
      const result = await signin(email, password)
      if (result?.otpRequired) {
        setOtpEmail(result.email)
        setOtpStep(true)
      }
    } catch (err) {
      const data = err.response?.data || {}
      if (data.unverified) {
        setUnverified(true)
        setError('Your email is not verified yet.')
      } else {
        setError(data.error || 'Failed to sign in')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleOtpChange = (index, value) => {
    if (!/^\d?$/.test(value)) return
    const next = [...otp]
    next[index] = value
    setOtp(next)
    if (value && index < 5) {
      otpRefs.current[index + 1]?.focus()
    }
  }

  const handleOtpKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !otp[index] && index > 0) {
      otpRefs.current[index - 1]?.focus()
    }
  }

  const handleOtpPaste = (e) => {
    const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6)
    if (pasted.length === 6) {
      setOtp(pasted.split(''))
      otpRefs.current[5]?.focus()
    }
  }

  const handleOtpSubmit = async (e) => {
    e.preventDefault()
    const code = otp.join('')
    if (code.length < 6) { setError('Enter the full 6-digit code'); return }
    setLoading(true); setError('')
    try {
      await verifyOtp(otpEmail, code, useAuthApp)
    } catch (err) {
      const data = err.response?.data || {}
      if (data.expired) {
        setError('Code expired. Please sign in again.')
        setOtpStep(false)
        setOtp(['', '', '', '', '', ''])
      } else {
        setError(data.error || 'Invalid code')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleResend = async () => {
    setResendLoading(true)
    try {
      await axios.post('/api/auth/resend-verification', { email })
      setResendDone(true)
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to resend verification email')
    } finally {
      setResendLoading(false)
    }
  }

  const gradientBg = (
    <>
      <div className="absolute -top-40 left-1/2 -translate-x-1/2 w-[720px] h-[480px] bg-gradient-to-b from-primary-container/20 via-secondary-container/10 to-transparent blur-3xl pointer-events-none rounded-full" />
      <div className="absolute top-1/3 -left-32 w-80 h-80 bg-tertiary-container/15 blur-3xl pointer-events-none rounded-full" />
      <div className="absolute bottom-10 -right-24 w-96 h-96 bg-secondary-container/20 blur-3xl pointer-events-none rounded-full" />
    </>
  )

  const logo = (
    <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-primary-container to-secondary flex items-center justify-center shadow-lg mb-4">
      <svg className="w-6 h-6 text-on-primary" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" viewBox="0 0 24 24">
        <path d="M12 2L2 7l10 5 10-5-10-5z" /><path d="M2 17l10 5 10-5" /><path d="M2 12l10 5 10-5" />
      </svg>
    </div>
  )

  if (otpStep) {
    return (
      <div className="bg-background min-h-screen flex flex-col justify-center items-center text-on-surface antialiased">
        <main className="w-full flex justify-center items-center">
          <div className="flex flex-col w-full items-center justify-center py-10 px-4 relative overflow-hidden">
            {gradientBg}
            <div className="relative w-full max-w-[480px] z-10">
              <div className="bg-surface-container/90 backdrop-blur-xl rounded-3xl p-8 shadow-xl flex flex-col">
                <div className="flex flex-col items-center text-center">
                  {logo}
                  <h1 className="text-xl font-semibold">
                    {useAuthApp ? 'Authenticator App' : 'Check your email'}
                  </h1>
                  <p className="text-sm text-on-surface-variant mt-1.5">
                    {useAuthApp
                      ? 'Enter the 6-digit code from your authenticator app.'
                      : <>We sent a 6-digit code to <span className="text-on-surface font-medium">{otpEmail}</span></>}
                  </p>
                </div>

                {/* toggle */}
                <button
                  type="button"
                  onClick={() => { setUseAuthApp(v => !v); setOtp(['','','','','','']); setError('') }}
                  className="mt-4 text-xs text-on-surface-variant hover:text-on-surface underline text-center"
                >
                  {useAuthApp ? "Use email code instead" : "Use authenticator app instead"}
                </button>
                {error && (
                  <div className="mt-6 p-3 bg-error/10 border border-error/20 rounded-lg">
                    <p className="text-sm text-error">{error}</p>
                  </div>
                )}

                <form className="flex flex-col gap-6 mt-6" onSubmit={handleOtpSubmit}>
                  <div className="flex gap-2 justify-center" onPaste={handleOtpPaste}>
                    {otp.map((digit, i) => (
                      <input
                        key={i}
                        ref={el => otpRefs.current[i] = el}
                        type="text"
                        inputMode="numeric"
                        maxLength={1}
                        value={digit}
                        onChange={e => handleOtpChange(i, e.target.value)}
                        onKeyDown={e => handleOtpKeyDown(i, e)}
                        className="w-11 h-14 text-center text-xl font-bold bg-surface-container-lowest text-on-surface rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                      />
                    ))}
                  </div>

                  <button type="submit" disabled={loading}
                    className="w-full py-2.5 px-4 rounded-lg bg-primary hover:bg-primary-fixed text-on-primary font-semibold disabled:opacity-50 disabled:cursor-not-allowed">
                    {loading ? 'Verifying...' : 'Verify & Sign In'}
                  </button>
                </form>

                <div className="mt-4 text-center">
                  <button
                    onClick={() => { setOtpStep(false); setOtp(['', '', '', '', '', '']); setError('') }}
                    className="text-sm text-on-surface-variant hover:text-on-surface"
                  >
                    ← Back to sign in
                  </button>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    )
  }

  return (
    <div className="bg-background min-h-screen flex flex-col justify-center items-center text-on-surface antialiased">
      <main className="w-full flex justify-center items-center">
        <div className="flex flex-col w-full items-center justify-center py-10 px-4 relative overflow-hidden">
          {gradientBg}

          <div className="relative w-full max-w-[480px] z-10">
            <div className="bg-surface-container/90 backdrop-blur-xl rounded-3xl p-8 shadow-xl flex flex-col">
              <div className="flex flex-col items-center text-center">
                {logo}
                <h1 className="text-xl font-semibold">Welcome back</h1>
                <p className="text-sm text-on-surface-variant mt-1.5">Sign in to your account</p>
              </div>

              {error && (
                <div className="mt-6 p-3 bg-error/10 border border-error/20 rounded-lg">
                  <p className="text-sm text-error">{error}</p>
                  {unverified && !resendDone && (
                    <button
                      onClick={handleResend}
                      disabled={resendLoading}
                      className="mt-2 text-sm text-tertiary hover:underline disabled:opacity-50"
                    >
                      {resendLoading ? 'Sending...' : 'Resend verification email'}
                    </button>
                  )}
                  {resendDone && (
                    <p className="mt-2 text-sm text-tertiary">Verification email sent — check your inbox.</p>
                  )}
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

                <button type="submit" disabled={loading}
                  className="w-full mt-3 py-2.5 px-4 rounded-lg bg-primary hover:bg-primary-fixed text-on-primary font-semibold disabled:opacity-50 disabled:cursor-not-allowed">
                  {loading ? 'Signing in...' : 'Sign In'}
                </button>
              </form>

              <div className="mt-6 text-center">
                <p className="text-sm text-on-surface-variant">
                  Don't have an account?{' '}
                  <Link to="/signup" className="text-tertiary hover:text-tertiary-fixed font-medium">Create account</Link>
                </p>
              </div>

              {GOOGLE_CLIENT_ID && (
                <>
                  <div className="flex items-center gap-3 my-4">
                    <div className="flex-1 h-px bg-outline-variant/40" />
                    <span className="text-xs text-on-surface-variant">or</span>
                    <div className="flex-1 h-px bg-outline-variant/40" />
                  </div>
                  <div id="google-signin-btn" className="flex justify-center" />
                </>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
