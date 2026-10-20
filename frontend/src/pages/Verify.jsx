import React, { useEffect, useState } from 'react'
import { useNavigate, useSearchParams, Link } from 'react-router-dom'
import axios from '../utils/axios'
import { useAuth } from '../context/AuthContext'

export default function Verify() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { setUserFromToken } = useAuth()

  const [status, setStatus] = useState('verifying') // verifying | success | error | expired
  const [error, setError] = useState('')
  const [resendEmail, setResendEmail] = useState('')
  const [resendLoading, setResendLoading] = useState(false)
  const [resendDone, setResendDone] = useState(false)

  useEffect(() => {
    const token = searchParams.get('token')
    if (!token) { setStatus('error'); setError('No token provided.'); return }

    axios.get(`/api/auth/verify?token=${token}`)
      .then(res => {
        setUserFromToken(res.data.token, res.data.user)
        setStatus('success')
        setTimeout(() => navigate('/dashboard'), 2000)
      })
      .catch(err => {
        const data = err.response?.data || {}
        if (data.expired) {
          setStatus('expired')
        } else {
          setStatus('error')
          setError(data.error || 'Verification failed.')
        }
      })
  }, [])

  const handleResend = async (e) => {
    e.preventDefault()
    setResendLoading(true)
    try {
      await axios.post('/api/auth/resend-verification', { email: resendEmail })
      setResendDone(true)
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to resend.')
    } finally {
      setResendLoading(false)
    }
  }

  return (
    <div className="bg-background min-h-screen flex flex-col justify-center items-center text-on-surface antialiased px-4">
      <div className="bg-surface-container/90 backdrop-blur-xl rounded-3xl p-8 shadow-xl w-full max-w-md text-center">

        {status === 'verifying' && (
          <>
            <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="text-on-surface-variant">Verifying your email…</p>
          </>
        )}

        {status === 'success' && (
          <>
            <div className="w-14 h-14 rounded-full bg-tertiary/20 flex items-center justify-center mx-auto mb-4">
              <svg className="w-7 h-7 text-tertiary" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold mb-2">Email verified!</h2>
            <p className="text-on-surface-variant text-sm">Redirecting you to the dashboard…</p>
          </>
        )}

        {(status === 'error') && (
          <>
            <div className="w-14 h-14 rounded-full bg-error/10 flex items-center justify-center mx-auto mb-4">
              <svg className="w-7 h-7 text-error" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold mb-2">Verification failed</h2>
            <p className="text-on-surface-variant text-sm mb-6">{error}</p>
            <Link to="/signin" className="text-tertiary text-sm hover:underline">Back to Sign In</Link>
          </>
        )}

        {status === 'expired' && (
          <>
            <div className="w-14 h-14 rounded-full bg-error/10 flex items-center justify-center mx-auto mb-4">
              <svg className="w-7 h-7 text-error" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold mb-2">Link expired</h2>
            <p className="text-on-surface-variant text-sm mb-6">Your verification link has expired. Enter your email to get a new one.</p>

            {resendDone ? (
              <p className="text-tertiary text-sm">New verification email sent. Check your inbox.</p>
            ) : (
              <form onSubmit={handleResend} className="flex flex-col gap-3">
                <input
                  type="email"
                  required
                  placeholder="your@email.com"
                  value={resendEmail}
                  onChange={e => setResendEmail(e.target.value)}
                  className="w-full bg-surface-container-lowest text-on-surface placeholder:text-outline-variant px-3.5 py-2.5 rounded-lg focus:outline-none"
                />
                <button
                  type="submit"
                  disabled={resendLoading}
                  className="w-full py-2.5 rounded-lg bg-primary text-on-primary font-semibold disabled:opacity-50"
                >
                  {resendLoading ? 'Sending…' : 'Resend verification email'}
                </button>
              </form>
            )}
          </>
        )}
      </div>
    </div>
  )
}
