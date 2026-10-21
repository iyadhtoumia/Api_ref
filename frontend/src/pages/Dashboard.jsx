import React, { useState, useEffect, useCallback, useRef } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import ThemeSettings from '../components/ThemeSettings'
import axios from '../utils/axios'

// ── icons ────────────────────────────────────────────────────────────────────
const Icon = {
  Home: () => <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M3 12l2-2m0 0l7-7 7 7m-14 0v9a1 1 0 001 1h4v-5h4v5h4a1 1 0 001-1v-9m-14 0h14" /></svg>,
  Bulk: () => <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>,
  Orders: () => <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" /></svg>,
  Api: () => <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" /></svg>,
  Support: () => <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M18.364 5.636l-3.536 3.536m0 5.656l3.536 3.536M9.172 9.172L5.636 5.636m3.536 9.192l-3.536 3.536M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-5 0a4 4 0 11-8 0 4 4 0 018 0z" /></svg>,
  Euro: () => <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M14.121 15.536c-1.171 1.952-3.07 1.952-4.242 0-1.172-1.953-1.172-5.119 0-7.072 1.171-1.952 3.07-1.952 4.242 0M8 10.5h4m-4 3h4" /></svg>,
  User: () => <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>,
  Search: () => <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>,
  Download: () => <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>,
  Copy: () => <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>,
  Close: () => <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>,
  Check: () => <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" /></svg>,
}

const YEARS = [2026, 2025, 2024]

// ── Service Picker Modal ──────────────────────────────────────────────────────
function ServicePicker({ serial, onConfirm, onCancel }) {
  const [services, setServices] = useState([])
  const [grouped, setGrouped] = useState({})
  const [search, setSearch] = useState('')
  const [selected, setSelected] = useState(null)
  const [loadingServices, setLoadingServices] = useState(true)
  const searchRef = useRef(null)

  useEffect(() => {
    setLoadingServices(true)
    axios.get('/api/services').then(res => {
      setServices(res.data.services || [])
    }).finally(() => setLoadingServices(false))
    setTimeout(() => searchRef.current?.focus(), 50)
  }, [])

  // group + filter
  useEffect(() => {
    const q = search.toLowerCase()
    const filtered = services.filter(s =>
      !q || s.name.toLowerCase().includes(q) || String(s.id).includes(q)
    )
    const g = {}
    for (const s of filtered) {
      if (!g[s.category]) g[s.category] = []
      g[s.category].push(s)
    }
    setGrouped(g)
  }, [services, search])

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-2xl flex flex-col max-h-[85vh]">

        {/* header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100 dark:border-gray-700">
          <div>
            <h2 className="font-semibold text-gray-900 dark:text-gray-100">Choose a service</h2>
            <p className="text-xs text-gray-400 mt-0.5 font-mono">{serial}</p>
          </div>
          <button onClick={onCancel} className="text-gray-400 hover:text-gray-600 p-1"><Icon.Close /></button>
        </div>

        {/* search */}
        <div className="px-5 py-3 border-b border-gray-100 dark:border-gray-700">
          <div className="relative">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"><Icon.Search /></span>
            <input
              ref={searchRef}
              type="text"
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Search by name or ID…"
              className="w-full pl-9 pr-4 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-300"
            />
          </div>
        </div>

        {/* service list */}
        <div className="overflow-y-auto flex-1 px-2 py-2">
          {loadingServices && <p className="text-center text-gray-400 text-sm py-8">Loading services…</p>}
          {!loadingServices && Object.keys(grouped).length === 0 && (
            <p className="text-center text-gray-400 text-sm py-8">No services found.</p>
          )}
          {!loadingServices && Object.entries(grouped).map(([category, items]) => (
            <div key={category} className="mb-3">
              <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider px-3 py-1.5">{category}</p>
              {items.map(svc => {
                const isSelected = selected?.id === svc.id
                return (
                  <button
                    key={svc.id}
                    onClick={() => setSelected(svc)}
                    className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm transition-colors mb-0.5 ${
                      isSelected ? 'bg-gray-900 text-white' : 'hover:bg-gray-50 text-gray-700'
                    }`}
                  >
                    <div className="flex items-center gap-3 text-left">
                      <span className={`text-xs font-mono w-8 shrink-0 ${isSelected ? 'text-gray-300' : 'text-gray-400'}`}>
                        {svc.id}
                      </span>
                      <span className="font-medium">{svc.name}</span>
                    </div>
                    <div className="flex items-center gap-3 shrink-0 ml-4">
                      <span className={`font-semibold tabular-nums ${isSelected ? 'text-white' : 'text-gray-800'}`}>
                        €{svc.price.toFixed(3)}
                      </span>
                      {isSelected && <Icon.Check />}
                    </div>
                  </button>
                )
              })}
            </div>
          ))}
        </div>

        {/* footer */}
        <div className="px-5 py-4 border-t border-gray-100 dark:border-gray-700 flex items-center justify-between gap-3">
          <div className="text-sm text-gray-500">
            {selected
              ? <span>Selected: <strong className="text-gray-900 dark:text-gray-100">{selected.name}</strong> — €{selected.price.toFixed(3)}</span>
              : 'No service selected'}
          </div>
          <div className="flex gap-2">
            <button onClick={onCancel} className="px-4 py-2 text-sm rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50">
              Cancel
            </button>
            <button
              disabled={!selected}
              onClick={() => onConfirm(selected)}
              className="px-5 py-2 text-sm rounded-lg bg-gray-900 text-white font-semibold hover:bg-gray-700 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Run Check
            </button>
          </div>
        </div>

      </div>
    </div>
  )
}

// ── Top-Up Modal ──────────────────────────────────────────────────────────────
const PRESET_AMOUNTS = [5, 10, 20, 50]

function TopUpModal({ onClose }) {
  const [method, setMethod] = useState('stripe') // 'stripe' | 'paypal'
  const [amount, setAmount] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handlePreset = (v) => setAmount(String(v))

  const handleSubmit = async (e) => {
    e.preventDefault()
    const val = parseFloat(amount)
    if (!val || val < 1) { setError('Minimum top-up is €1.00'); return }
    setError('')
    setLoading(true)
    try {
      if (method === 'stripe') {
        const res = await axios.post('/api/payments/create-checkout', { amount_eur: val })
        window.location.href = res.data.checkout_url
      } else {
        const res = await axios.post('/api/payments/paypal/create-order', { amount_eur: val })
        window.location.href = res.data.approve_url
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to start checkout')
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-sm p-6">
        <div className="flex items-center justify-between mb-5">
          <h2 className="font-semibold text-gray-900 dark:text-gray-100">Add funds</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"><Icon.Close /></button>
        </div>

        {/* Payment method toggle */}
        <div className="flex gap-2 mb-5 p-1 bg-gray-100 rounded-xl">
          <button
            type="button"
            onClick={() => { setMethod('stripe'); setError('') }}
            className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-lg text-sm font-semibold transition-colors ${method === 'stripe' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
          >
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
              <path d="M13.976 9.15c-2.172-.806-3.356-1.426-3.356-2.409 0-.831.683-1.305 1.901-1.305 2.227 0 4.515.858 6.09 1.631l.89-5.494C18.252.975 15.697 0 12.165 0 9.667 0 7.589.654 6.104 1.872 4.56 3.147 3.757 4.992 3.757 7.218c0 4.039 2.467 5.76 6.476 7.219 2.585.92 3.445 1.574 3.445 2.583 0 .98-.84 1.545-2.354 1.545-1.875 0-4.965-.921-6.99-2.109l-.9 5.555C5.175 22.99 8.385 24 11.714 24c2.641 0 4.843-.624 6.328-1.813 1.664-1.305 2.525-3.236 2.525-5.732 0-4.128-2.524-5.851-6.591-7.305z"/>
            </svg>
            Stripe
          </button>
          <button
            type="button"
            onClick={() => { setMethod('paypal'); setError('') }}
            className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-lg text-sm font-semibold transition-colors ${method === 'paypal' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
          >
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="#003087">
              <path d="M7.076 21.337H2.47a.641.641 0 0 1-.633-.74L4.944.901C5.026.382 5.474 0 5.998 0h7.46c2.57 0 4.578.543 5.69 1.81 1.01 1.15 1.304 2.42 1.012 4.287-.023.143-.047.288-.077.437-.983 5.05-4.349 6.797-8.647 6.797h-2.19c-.524 0-.968.382-1.05.9l-1.12 7.106zm14.146-14.42a3.35 3.35 0 0 0-.607-.541c-.013.076-.026.175-.041.26-.983 5.05-4.349 6.797-8.647 6.797h-2.19c-.524 0-.968.382-1.05.9l-1.12 7.106H2.47a.641.641 0 0 1-.633-.74L4.944.901C5.026.382 5.474 0 5.998 0h7.46c2.57 0 4.578.543 5.69 1.81.944 1.074 1.27 2.267 1.074 4.107z"/>
            </svg>
            PayPal
          </button>
        </div>

        <div className="flex gap-2 mb-4">
          {PRESET_AMOUNTS.map(v => (
            <button key={v} type="button" onClick={() => handlePreset(v)}
              className={`flex-1 py-2 rounded-lg text-sm font-semibold border transition-colors ${amount === String(v) ? 'bg-gray-900 text-white border-gray-900' : 'border-gray-200 text-gray-600 hover:bg-gray-50'}`}>
              €{v}
            </button>
          ))}
        </div>
        <form onSubmit={handleSubmit}>
          <div className="relative mb-4">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm font-medium">€</span>
            <input
              type="number" min="1" step="0.01"
              value={amount}
              onChange={e => setAmount(e.target.value)}
              placeholder="Custom amount"
              className="w-full pl-7 pr-4 py-2.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-300"
            />
          </div>
          {error && <p className="text-sm text-red-600 mb-3">{error}</p>}
          <button type="submit" disabled={loading || !amount}
            className={`w-full py-2.5 rounded-lg text-sm font-semibold disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2 text-white transition-colors ${
              method === 'paypal'
                ? 'bg-[#003087] hover:bg-[#002069]'
                : 'bg-gray-900 hover:bg-gray-700'
            }`}>
            {loading
              ? <><span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />Redirecting…</>
              : method === 'paypal' ? 'Pay with PayPal' : 'Pay with Stripe'}
          </button>
        </form>
      </div>
    </div>
  )
}

// ── TOTP / Authenticator Section ─────────────────────────────────────────────
function TotpSection({ user, refreshUser }) {
  const [step, setStep] = useState('idle') // idle | setup | verify | disable
  const [qr, setQr] = useState('')
  const [secret, setSecret] = useState('')
  const [code, setCode] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const startSetup = async () => {
    setError(''); setLoading(true)
    try {
      const res = await axios.post('/api/auth/totp/setup')
      setQr(res.data.qr)
      setSecret(res.data.secret)
      setStep('setup')
    } catch { setError('Failed to start setup') }
    finally { setLoading(false) }
  }

  const confirmEnable = async (e) => {
    e.preventDefault(); setError(''); setLoading(true)
    try {
      await axios.post('/api/auth/totp/enable', { code })
      await refreshUser()
      setStep('idle'); setSuccess('Authenticator app enabled')
      setTimeout(() => setSuccess(''), 3000)
    } catch (err) { setError(err.response?.data?.error || 'Invalid code') }
    finally { setLoading(false) }
  }

  const confirmDisable = async (e) => {
    e.preventDefault(); setError(''); setLoading(true)
    try {
      await axios.post('/api/auth/totp/disable', { password })
      await refreshUser()
      setStep('idle'); setSuccess('Authenticator app removed')
      setTimeout(() => setSuccess(''), 3000)
    } catch (err) { setError(err.response?.data?.error || 'Failed') }
    finally { setLoading(false) }
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
      <div className="px-6 py-4 border-b border-gray-100 dark:border-gray-700 flex items-center justify-between">
        <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Authenticator App</p>
        {user?.totp_enabled && (
          <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full font-medium">Active</span>
        )}
      </div>

      <div className="px-6 py-4">
        {success && <p className="text-sm text-green-600 mb-3">{success}</p>}
        {error && <p className="text-sm text-red-500 mb-3">{error}</p>}

        {step === 'idle' && (
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-800">
                {user?.totp_enabled ? 'Google Authenticator is active' : 'Not set up'}
              </p>
              <p className="text-xs text-gray-400 mt-0.5">
                {user?.totp_enabled
                  ? 'Use it as a fallback if you lose access to your email.'
                  : 'Use Google Authenticator or Authy as a 2FA fallback.'}
              </p>
            </div>
            {user?.totp_enabled ? (
              <button onClick={() => { setStep('disable'); setError('') }}
                className="text-sm text-red-500 border border-red-200 px-3 py-1.5 rounded-lg hover:bg-red-50">
                Remove
              </button>
            ) : (
              <button onClick={startSetup} disabled={loading}
                className="text-sm text-gray-700 border border-gray-200 px-3 py-1.5 rounded-lg hover:bg-gray-50 disabled:opacity-50">
                {loading ? 'Loading…' : 'Set Up'}
              </button>
            )}
          </div>
        )}

        {step === 'setup' && (
          <div className="space-y-4">
            <p className="text-sm text-gray-600">
              Scan this QR code with <strong>Google Authenticator</strong> or <strong>Authy</strong>, then enter the 6-digit code to confirm.
            </p>
            <div className="flex justify-center">
              <img src={qr} alt="TOTP QR Code" className="w-44 h-44 rounded-lg border border-gray-200" />
            </div>
            <p className="text-xs text-gray-400 text-center">
              Can't scan? Enter this key manually: <span className="font-mono text-gray-700">{secret}</span>
            </p>
            <form onSubmit={confirmEnable} className="flex gap-2">
              <input type="text" inputMode="numeric" maxLength={6} value={code}
                onChange={e => setCode(e.target.value.replace(/\D/g, ''))}
                placeholder="6-digit code"
                className="flex-1 border border-gray-200 rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-gray-300" />
              <button type="submit" disabled={loading || code.length < 6}
                className="px-4 py-2 rounded-lg bg-gray-900 text-white text-sm font-semibold hover:bg-gray-700 disabled:opacity-40">
                {loading ? 'Verifying…' : 'Confirm'}
              </button>
            </form>
            <button onClick={() => { setStep('idle'); setError('') }}
              className="text-xs text-gray-400 hover:text-gray-600">Cancel</button>
          </div>
        )}

        {step === 'disable' && (
          <form onSubmit={confirmDisable} className="space-y-3">
            <p className="text-sm text-gray-600">Enter your password to remove the authenticator app.</p>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)} required
              placeholder="Your password"
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-300" />
            <div className="flex gap-2">
              <button type="button" onClick={() => { setStep('idle'); setError('') }}
                className="flex-1 py-2 rounded-lg border border-gray-200 text-sm text-gray-600 hover:bg-gray-50">Cancel</button>
              <button type="submit" disabled={loading}
                className="flex-1 py-2 rounded-lg bg-red-600 text-white text-sm font-semibold hover:bg-red-700 disabled:opacity-40">
                {loading ? 'Removing…' : 'Remove'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}

// ── Settings helpers ──────────────────────────────────────────────────────────
function InfoRow({ label, value, valueClass = 'text-gray-800' }) {
  return (
    <div className="flex items-center justify-between py-4">
      <p className="text-sm text-gray-500">{label}</p>
      <p className={`text-sm font-medium ${valueClass}`}>{value}</p>
    </div>
  )
}

function SettingsRow({ label, value, editContent: EditContent }) {
  const [editing, setEditing] = useState(false)
  return (
    <div className="px-6 py-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs text-gray-400">{label}</p>
          <p className="text-sm font-medium text-gray-800 mt-0.5">{value}</p>
        </div>
        {!editing && (
          <button onClick={() => setEditing(true)} className="text-sm text-gray-600 border border-gray-200 px-3 py-1.5 rounded-lg hover:bg-gray-50">
            Change
          </button>
        )}
      </div>
      {editing && <EditContent onDone={() => setEditing(false)} />}
    </div>
  )
}

// ── Support Modal ─────────────────────────────────────────────────────────────
function SupportModal({ onClose }) {
  const [subject, setSubject] = useState('')
  const [description, setDescription] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!description.trim()) { setError('Please describe your issue'); return }
    setError('')
    setLoading(true)
    try {
      await axios.post('/api/support', { subject, description })
      setSuccess(true)
      setTimeout(onClose, 2000)
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to send. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-md p-6">
        <div className="flex items-center justify-between mb-5">
          <h2 className="font-semibold text-gray-900 dark:text-gray-100">Contact Support</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"><Icon.Close /></button>
        </div>
        {success ? (
          <div className="flex flex-col items-center gap-3 py-6 text-green-600">
            <Icon.Check />
            <p className="text-sm font-medium">Message sent — we'll get back to you shortly</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs text-gray-500 mb-1">Subject <span className="text-gray-400">(optional)</span></label>
              <input
                type="text"
                value={subject}
                onChange={e => setSubject(e.target.value)}
                placeholder="e.g. Payment issue, Wrong result…"
                className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-gray-300"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">Description</label>
              <textarea
                value={description}
                onChange={e => setDescription(e.target.value)}
                required
                rows={5}
                placeholder="Describe your issue in detail…"
                className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-gray-300 resize-none"
              />
            </div>
            {error && <p className="text-sm text-red-600">{error}</p>}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 rounded-lg text-sm font-semibold bg-gray-900 text-white hover:bg-gray-700 disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {loading
                ? <><span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />Sending…</>
                : 'Send Message'}
            </button>
          </form>
        )}
      </div>
    </div>
  )
}

// ── Change Password Modal ─────────────────────────────────────────────────────
function ChangePasswordModal({ onClose }) {
  const [currentPw, setCurrentPw] = useState('')
  const [newPw, setNewPw] = useState('')
  const [confirmPw, setConfirmPw] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (newPw !== confirmPw) { setError('New passwords do not match'); return }
    if (newPw.length < 8) { setError('New password must be at least 8 characters'); return }
    setError('')
    setLoading(true)
    try {
      await axios.post('/api/auth/change-password', { current_password: currentPw, new_password: newPw })
      setSuccess(true)
      setTimeout(onClose, 1500)
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to change password')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-sm p-6">
        <div className="flex items-center justify-between mb-5">
          <h2 className="font-semibold text-gray-900 dark:text-gray-100">Change Password</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"><Icon.Close /></button>
        </div>
        {success ? (
          <div className="flex flex-col items-center gap-3 py-4 text-green-600">
            <Icon.Check />
            <p className="text-sm font-medium">Password updated successfully</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs text-gray-500 mb-1">Current Password</label>
              <input type="password" value={currentPw} onChange={e => setCurrentPw(e.target.value)} required
                className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-gray-300" />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">New Password</label>
              <input type="password" value={newPw} onChange={e => setNewPw(e.target.value)} required minLength={8}
                className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-gray-300" />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">Confirm New Password</label>
              <input type="password" value={confirmPw} onChange={e => setConfirmPw(e.target.value)} required
                className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-gray-300" />
            </div>
            {error && <p className="text-sm text-red-600">{error}</p>}
            <button type="submit" disabled={loading}
              className="w-full py-2.5 rounded-lg text-sm font-semibold bg-gray-900 text-white hover:bg-gray-700 disabled:opacity-50 flex items-center justify-center gap-2">
              {loading ? <><span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />Updating…</> : 'Update Password'}
            </button>
          </form>
        )}
      </div>
    </div>
  )
}

// ── Main Dashboard ────────────────────────────────────────────────────────────
export default function Dashboard() {
  const { user, signout, refreshUser } = useAuth()

  // lookup
  const [serial, setSerial] = useState('')
  const [showPicker, setShowPicker] = useState(false)
  const [loading, setLoading] = useState(false)
  const [configResult, setConfigResult] = useState(null)
  const [lookupError, setLookupError] = useState('')

  // history
  const [activeYear, setActiveYear] = useState(2026)
  const [searchQuery, setSearchQuery] = useState('')
  const [history, setHistory] = useState([])
  const [historyTotal, setHistoryTotal] = useState(0)
  const [historyPage, setHistoryPage] = useState(1)
  const [historyPages, setHistoryPages] = useState(1)
  const [historyLoading, setHistoryLoading] = useState(false)
  const [copiedId, setCopiedId] = useState(null)

  const [activeNav, setActiveNav] = useState('home')
  const [showTopUp, setShowTopUp] = useState(false)
  const [paymentToast, setPaymentToast] = useState('')
  const [tgToken, setTgToken] = useState('')
  const [tgTokenLoading, setTgTokenLoading] = useState(false)
  const [showUserMenu, setShowUserMenu] = useState(false)
  const [showChangePassword, setShowChangePassword] = useState(false)
  const [showSupport, setShowSupport] = useState(false)
  const userMenuRef = useRef(null)

  // close user menu on outside click
  useEffect(() => {
    const handler = (e) => {
      if (userMenuRef.current && !userMenuRef.current.contains(e.target)) {
        setShowUserMenu(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])
  const fetchHistory = useCallback(async (year, search, page) => {
    setHistoryLoading(true)
    try {
      const params = new URLSearchParams({ year, page })
      if (search) params.set('search', search)
      const res = await axios.get(`/api/history?${params}`)
      setHistory(res.data.history || [])
      setHistoryTotal(res.data.total || 0)
      setHistoryPages(res.data.pages || 1)
    } catch {
      setHistory([])
    } finally {
      setHistoryLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchHistory(activeYear, searchQuery, historyPage)
  }, [activeYear, historyPage, fetchHistory])

  // Handle payment redirect back (Stripe + PayPal)
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const status = params.get('payment')
    const provider = params.get('provider')
    const sessionId = params.get('session_id')
    const paymentId = params.get('paymentId')
    const payerId = params.get('PayerID')

    if (status === 'success') {
      window.history.replaceState({}, '', '/dashboard')

      if (provider === 'paypal' && paymentId && payerId) {
        // Capture PayPal payment
        axios.post('/api/payments/paypal/capture-order', { paymentId, PayerID: payerId })
          .then(() => refreshUser())
          .catch(() => refreshUser())
          .finally(() => {
            setPaymentToast('Payment successful! Your balance has been updated.')
            setTimeout(() => setPaymentToast(''), 5000)
          })
      } else if (sessionId) {
        // Verify Stripe session
        axios.post('/api/payments/verify-session', { session_id: sessionId })
          .then(() => refreshUser())
          .catch(() => refreshUser())
          .finally(() => {
            setPaymentToast('Payment successful! Your balance has been updated.')
            setTimeout(() => setPaymentToast(''), 5000)
          })
      } else {
        refreshUser()
        setPaymentToast('Payment successful! Your balance has been updated.')
        setTimeout(() => setPaymentToast(''), 5000)
      }
    } else if (status === 'cancel') {
      setPaymentToast('Payment cancelled.')
      window.history.replaceState({}, '', '/dashboard')
      setTimeout(() => setPaymentToast(''), 4000)
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const handleSearchHistory = (e) => {
    e.preventDefault()
    setHistoryPage(1)
    fetchHistory(activeYear, searchQuery, 1)
  }

  // step 1: validate serial, open picker
  const handleSerialSubmit = (e) => {
    e.preventDefault()
    if (serial.length < 4) { setLookupError('Serial too short.'); return }
    setLookupError('')
    setConfigResult(null)
    setShowPicker(true)
  }

  // step 2: service chosen, run lookup
  const handleServiceConfirm = async (service) => {
    setShowPicker(false)
    setLoading(true)
    setLookupError('')
    setConfigResult(null)
    try {
      const res = await axios.post('/api/lookup-config', { serial, service_id: service.id })
      setConfigResult(res.data)
      await refreshUser()
      fetchHistory(activeYear, searchQuery, 1)
      setHistoryPage(1)
    } catch (err) {
      setLookupError(err.response?.data?.error || 'Lookup failed')
    } finally {
      setLoading(false)
    }
  }

  const generateTgToken = async () => {
    setTgTokenLoading(true)
    setTgToken('')
    try {
      const res = await axios.post('/api/auth/telegram-link-token')
      setTgToken(res.data.token)
    } catch {
      setTgToken('error')
    } finally {
      setTgTokenLoading(false)
    }
  }

  const unlinkTelegram = async () => {
    try {
      await axios.post('/api/auth/telegram-unlink')
      await refreshUser()
    } catch { /* ignore */ }
  }

  // exports
  const exportHTML = () => {
    const rows = history.map(h => `<tr><td>#${h.id}</td><td>${h.serial}</td><td>${h.service_name || ''}</td><td>${h.config}</td><td>${h.created_at}</td><td>€${(h.amount_eur / 100).toFixed(3)}</td></tr>`).join('')
    const html = `<html><body><table border="1"><thead><tr><th>Order</th><th>IMEI/Serial</th><th>Service</th><th>Result</th><th>Date</th><th>Cost</th></tr></thead><tbody>${rows}</tbody></table></body></html>`
    const blob = new Blob([html], { type: 'text/html' })
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = `history_${activeYear}.html`; a.click()
  }

  const exportCSV = () => {
    const lines = ['Order,IMEI/Serial,Service,Result,Date,Cost',
      ...history.map(h => `#${h.id},"${h.serial}","${h.service_name || ''}","${h.config}","${h.created_at}",${(h.amount_eur / 100).toFixed(3)}`)
    ]
    const blob = new Blob([lines.join('\n')], { type: 'text/csv' })
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = `history_${activeYear}.csv`; a.click()
  }

  const exportIMEIs = () => {
    const blob = new Blob([history.map(h => h.serial).join('\n')], { type: 'text/plain' })
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = `imeis_${activeYear}.txt`; a.click()
  }

  const copyToClipboard = (text, id) => {
    navigator.clipboard.writeText(text)
    setCopiedId(id)
    setTimeout(() => setCopiedId(null), 1500)
  }

  const fmtEUR = (cents) => `€${(cents / 100).toFixed(2)}`
  const username = user?.email?.split('@')[0] || 'User'

  const navItems = [
    { id: 'home', label: 'Home', icon: <Icon.Home /> },
    { id: 'bulk', label: 'Orders', icon: <Icon.Orders /> },
    { id: 'settings', label: 'Settings', icon: <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/><circle cx="12" cy="12" r="3"/></svg> },
  ]

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 text-gray-800 dark:text-gray-100">

      {/* top-up modal */}
      {showTopUp && <TopUpModal onClose={() => setShowTopUp(false)} />}

      {/* change password modal */}
      {showChangePassword && <ChangePasswordModal onClose={() => setShowChangePassword(false)} />}

      {/* support modal */}
      {showSupport && <SupportModal onClose={() => setShowSupport(false)} />}

      {/* payment toast */}
      {paymentToast && (
        <div className={`fixed top-4 left-1/2 -translate-x-1/2 z-50 px-5 py-3 rounded-xl shadow-lg text-sm font-medium transition-all ${paymentToast.includes('successful') ? 'bg-green-600 text-white' : 'bg-gray-800 text-white'}`}>
          {paymentToast}
        </div>
      )}

      {/* service picker modal */}
      {showPicker && (
        <ServicePicker
          serial={serial}
          onConfirm={handleServiceConfirm}
          onCancel={() => setShowPicker(false)}
        />
      )}

      {/* navbar */}
      <nav className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 flex items-center gap-1 h-14">
          {navItems.map(n => (
            <button key={n.id} onClick={() => setActiveNav(n.id)}
              className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${activeNav === n.id ? 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-gray-100' : 'text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800 hover:text-gray-700 dark:hover:text-gray-300'}`}>
              {n.icon}{n.label}
            </button>
          ))}
          <div className="flex-1" />
          <div className="flex items-center gap-1">
            <Link to="/faq" className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>FAQ</span>
            </Link>
            <button onClick={() => setShowSupport(true)} className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800"><Icon.Support /><span>Support</span></button>
            <Link to="/services" className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm text-gray-500 hover:bg-gray-50">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 10h16M4 14h16M4 18h16"/></svg>
              <span>Services</span>
            </Link>
            <div className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm text-gray-500 border border-gray-200 mx-1 cursor-pointer hover:bg-gray-50" onClick={() => setShowTopUp(true)} title="Add funds">
              <Icon.Euro /><span className="font-medium text-gray-700">{fmtEUR(user?.balance_eur || 0)}</span>
              <span className="text-xs text-gray-400 ml-0.5">+</span>
            </div>
            {/* user menu */}
            <div className="relative" ref={userMenuRef}>
              <button
                onClick={() => setShowUserMenu(v => !v)}
                className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm text-gray-500 hover:bg-gray-50"
              >
                <Icon.User /><span>{user?.email || username}</span>
                <svg className="w-3 h-3 ml-0.5 text-gray-400" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7"/></svg>
              </button>
              {showUserMenu && (
                <div className="absolute right-0 top-full mt-1 w-48 bg-white border border-gray-200 rounded-xl shadow-lg py-1 z-50">
                  <div className="px-4 py-2.5 border-b border-gray-100">
                    <p className="text-xs text-gray-400 truncate">{user?.email}</p>
                    <p className="text-sm font-semibold text-gray-800">{fmtEUR(user?.balance_eur || 0)}</p>
                  </div>
                  <button
                    onClick={() => { setShowUserMenu(false); setShowChangePassword(true) }}
                    className="w-full text-left flex items-center gap-2.5 px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
                  >
                    <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"/></svg>
                    Change Password
                  </button>
                  <button
                    onClick={() => { setShowUserMenu(false); setActiveNav('settings') }}
                    className="w-full text-left flex items-center gap-2.5 px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
                  >
                    <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/><circle cx="12" cy="12" r="3"/></svg>
                    Settings
                  </button>
                  {user?.is_admin && (
                    <Link
                      to="/admin"
                      onClick={() => setShowUserMenu(false)}
                      className="w-full flex items-center gap-2.5 px-4 py-2.5 text-sm text-indigo-600 hover:bg-indigo-50 transition-colors"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/></svg>
                      Admin Panel
                    </Link>
                  )}
                  <div className="border-t border-gray-100 mt-1">
                    <button
                      onClick={() => { setShowUserMenu(false); signout() }}
                      className="w-full text-left flex items-center gap-2.5 px-4 py-2.5 text-sm text-red-600 hover:bg-red-50 transition-colors"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/></svg>
                      Sign Out
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-5xl mx-auto px-4 py-8 space-y-8">

        {/* quick lookup */}
        {activeNav === 'home' && (
          <>
          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 shadow-sm">
            <h2 className="text-base font-semibold mb-1 dark:text-gray-100">New Check</h2>
            <p className="text-xs text-gray-400 dark:text-gray-500 mb-4">Enter an IMEI or serial, then select a service to run.</p>
            <form onSubmit={handleSerialSubmit} className="flex gap-3 flex-wrap">
              <input
                type="text"
                value={serial}
                onChange={e => { setSerial(e.target.value.toUpperCase()); setLookupError(''); setConfigResult(null) }}
                placeholder="Enter IMEI or serial number"
                className="flex-1 min-w-[200px] border border-gray-200 rounded-lg px-4 py-2.5 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-gray-300"
                required minLength={4} maxLength={20}
              />
              <button type="submit" disabled={loading}
                className="bg-gray-900 text-white px-6 py-2.5 rounded-lg text-sm font-semibold hover:bg-gray-700 disabled:opacity-50 flex items-center gap-2">
                {loading
                  ? <><span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />Checking…</>
                  : <><Icon.Search />Choose Service</>}
              </button>
            </form>

            {lookupError && <p className="mt-3 text-sm text-red-600">{lookupError}</p>}

            {configResult?.success && (
              <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg text-sm space-y-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-mono font-semibold">{configResult.serial}</span>
                  <span className="bg-gray-100 text-gray-600 text-xs px-2 py-0.5 rounded">{configResult.service_name}</span>
                  {configResult.cached && <span className="text-xs text-green-600 bg-green-100 px-2 py-0.5 rounded">Cached — free</span>}
                </div>
                <p className="text-gray-700">{configResult.config}</p>
              </div>
            )}
          </div>

          {/* Telegram account linking */}
          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 shadow-sm">
            <div className="flex items-center gap-3 mb-3">
              <svg className="w-5 h-5 text-[#229ED9] shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="22" y1="2" x2="11" y2="13"/>
                <polygon points="22 2 15 22 11 13 2 9 22 2"/>
              </svg>
              <h2 className="text-base font-semibold">Telegram Bot</h2>
              {user?.telegram_linked && (
                <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full font-medium">Connected</span>
              )}
            </div>

            {user?.telegram_linked ? (
              <div className="flex items-center gap-4">
                <p className="text-sm text-gray-500">Your Telegram account shares this balance and history.</p>
                <button onClick={unlinkTelegram}
                  className="text-xs text-red-500 hover:text-red-700 underline shrink-0">
                  Disconnect
                </button>
              </div>
            ) : (
              <div className="space-y-3">
                <p className="text-sm text-gray-500">
                  Use the same balance on{' '}
                  <a href="https://t.me/AppleConfigBot" target="_blank" rel="noopener noreferrer" className="text-[#229ED9] hover:underline">
                    @AppleConfigBot
                  </a>
                  {' '}by linking your account.
                </p>
                <div className="flex items-center gap-3 flex-wrap">
                  <button onClick={generateTgToken} disabled={tgTokenLoading}
                    className="bg-[#229ED9] hover:bg-[#1a8bbf] disabled:opacity-50 text-white px-4 py-2 rounded-lg text-sm font-semibold transition-colors">
                    {tgTokenLoading ? 'Generating…' : 'Generate Link Token'}
                  </button>
                  {tgToken && tgToken !== 'error' && (
                    <div className="flex items-center gap-2 bg-gray-50 border border-gray-200 rounded-lg px-3 py-2">
                      <code className="text-sm font-mono text-gray-800">/link {tgToken}</code>
                      <button onClick={() => navigator.clipboard.writeText(`/link ${tgToken}`)}
                        className="text-gray-400 hover:text-gray-600 text-xs">Copy</button>
                    </div>
                  )}
                  {tgToken === 'error' && <p className="text-sm text-red-500">Failed to generate token.</p>}
                </div>
                {tgToken && tgToken !== 'error' && (
                  <p className="text-xs text-gray-400">Token expires in 15 minutes. Send the command above to the bot.</p>
                )}
              </div>
            )}
          </div>
          </>
        )}

        {/* history */}
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm">
          <div className="px-6 py-5 border-b border-gray-100 dark:border-gray-700">
            <h2 className="text-base font-semibold text-center mb-4 dark:text-gray-100">IMEI / Serial check history</h2>

            <form onSubmit={handleSearchHistory} className="flex flex-wrap items-center gap-2 justify-center">
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"><Icon.Search /></span>
                <input type="text" value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
                  placeholder="Search IMEI or serial number"
                  className="pl-9 pr-4 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-300 w-64" />
              </div>
              <button type="submit" className="bg-gray-900 text-white px-4 py-2 rounded-lg text-sm font-semibold hover:bg-gray-700">Search</button>
              {YEARS.map(y => (
                <button key={y} type="button" onClick={() => { setActiveYear(y); setHistoryPage(1) }}
                  className={`px-4 py-2 rounded-lg text-sm font-semibold transition-colors ${activeYear === y ? 'bg-gray-900 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}>
                  {y}
                </button>
              ))}
            </form>

            <p className="text-center mt-4 text-sm">
              <span className="text-red-600 font-bold">{historyTotal}</span>
              <span className="text-gray-500"> completed orders in {activeYear}</span>
            </p>

            <div className="flex flex-wrap gap-2 justify-center mt-4">
              <button onClick={exportHTML} className="flex items-center gap-1.5 text-sm px-4 py-2 border border-gray-200 rounded-lg hover:bg-gray-50"><Icon.Download />HTML</button>
              <button onClick={exportCSV} className="flex items-center gap-1.5 text-sm px-4 py-2 border border-gray-200 rounded-lg hover:bg-gray-50"><Icon.Download />CSV</button>
              <button onClick={exportIMEIs} className="flex items-center gap-1.5 text-sm px-4 py-2 border border-gray-200 rounded-lg hover:bg-gray-50"><Icon.Download />IMEI's Only</button>
            </div>

            {historyPages > 1 && (
              <div className="flex items-center justify-center gap-2 mt-4 text-sm">
                {Array.from({ length: historyPages }, (_, i) => i + 1).map(p => (
                  <button key={p} onClick={() => setHistoryPage(p)}
                    className={`w-8 h-8 rounded-lg font-semibold transition-colors ${historyPage === p ? 'bg-red-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}>
                    {p}
                  </button>
                ))}
                {historyPage < historyPages && (
                  <button onClick={() => setHistoryPage(p => p + 1)} className="px-3 h-8 rounded-lg bg-gray-100 text-gray-600 hover:bg-gray-200 font-semibold">Next ›</button>
                )}
                <span className="text-gray-400 ml-2">
                  Showing {(historyPage - 1) * 250 + 1}–{Math.min(historyPage * 250, historyTotal)} of {historyTotal}
                </span>
              </div>
            )}
          </div>

          <div className="divide-y divide-gray-100">
            {historyLoading && <div className="py-12 text-center text-gray-400 text-sm">Loading…</div>}
            {!historyLoading && history.length === 0 && <div className="py-12 text-center text-gray-400 text-sm">No records found.</div>}
            {!historyLoading && history.map(item => {
              const costEUR = (item.amount_eur / 100).toFixed(3)
              return (
                <div key={item.id} className="px-5 py-4">
                  <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm">
                    <span className="font-bold text-blue-600 shrink-0">#{item.id}</span>
                    <span className="font-mono text-gray-700 shrink-0">IMEI {item.serial}</span>
                    <button onClick={() => copyToClipboard(item.serial, item.id)} className="text-gray-400 hover:text-gray-600 shrink-0" title="Copy IMEI">
                      {copiedId === item.id ? <span className="text-xs text-green-500">Copied!</span> : <Icon.Copy />}
                    </button>
                    <span className="text-gray-400 shrink-0">{item.created_at}</span>
                    <div className="flex-1" />
                    <span className="text-gray-400 shrink-0">IP {item.ip}</span>
                    <span className="bg-gray-100 text-gray-600 px-2 py-0.5 rounded text-xs font-medium shrink-0">
                      {item.service_name || 'Service 3'}
                    </span>
                    <span className="text-gray-600 shrink-0">Cost €{costEUR}</span>
                    <span className="text-gray-600 shrink-0">Balance {fmtEUR(user?.balance_eur || 0)}</span>
                  </div>
                  <div className="mt-2 text-sm bg-gray-50 rounded px-3 py-2 font-mono text-gray-700">
                    {item.serial}{' '}
                    {item.config.includes('Find My') ? (
                      <>{item.config.split('Find My')[0]}Find My
                        {item.config.includes('OFF') && <span className="ml-1 text-red-600 font-bold">OFF</span>}
                        {item.config.includes('ON') && !item.config.includes('OFF') && <span className="ml-1 text-green-600 font-bold">ON</span>}
                      </>
                    ) : item.config}
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* settings tab */}
        {activeNav === 'settings' && (
          <div className="space-y-4">

            {/* Profile */}
            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm">
              <div className="px-6 py-4 border-b border-gray-100">
                <p className="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">Profile</p>
              </div>
              <div className="divide-y divide-gray-100">

                {/* Email row */}
                <SettingsRow
                  label="Email"
                  value={user?.email}
                  editContent={({ onDone }) => {
                    const [newEmail, setNewEmail] = useState('')
                    const [pw, setPw] = useState('')
                    const [err, setErr] = useState('')
                    const [saving, setSaving] = useState(false)
                    const submit = async (e) => {
                      e.preventDefault()
                      setSaving(true); setErr('')
                      try {
                        await axios.post('/api/auth/change-email', { new_email: newEmail, password: pw })
                        await refreshUser()
                        onDone()
                      } catch (e) { setErr(e.response?.data?.error || 'Failed') }
                      finally { setSaving(false) }
                    }
                    return (
                      <form onSubmit={submit} className="space-y-3 pt-3">
                        <input type="email" value={newEmail} onChange={e => setNewEmail(e.target.value)} required
                          placeholder="New email address"
                          className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-300" />
                        <input type="password" value={pw} onChange={e => setPw(e.target.value)} required
                          placeholder="Confirm your password"
                          className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-300" />
                        {err && <p className="text-xs text-red-500">{err}</p>}
                        <div className="flex gap-2">
                          <button type="button" onClick={onDone} className="flex-1 py-2 rounded-lg border border-gray-200 text-sm text-gray-600 hover:bg-gray-50">Cancel</button>
                          <button type="submit" disabled={saving} className="flex-1 py-2 rounded-lg bg-gray-900 text-white text-sm font-semibold hover:bg-gray-700 disabled:opacity-40">
                            {saving ? 'Saving…' : 'Update Email'}
                          </button>
                        </div>
                      </form>
                    )
                  }}
                />

                {/* Password row */}
                <SettingsRow
                  label="Password"
                  value="••••••••"
                  editContent={({ onDone }) => {
                    const [cur, setCur] = useState('')
                    const [nw, setNw] = useState('')
                    const [cf, setCf] = useState('')
                    const [err, setErr] = useState('')
                    const [saving, setSaving] = useState(false)
                    const submit = async (e) => {
                      e.preventDefault()
                      if (nw !== cf) { setErr('Passwords do not match'); return }
                      setSaving(true); setErr('')
                      try {
                        await axios.post('/api/auth/change-password', { current_password: cur, new_password: nw })
                        onDone()
                      } catch (e) { setErr(e.response?.data?.error || 'Failed') }
                      finally { setSaving(false) }
                    }
                    return (
                      <form onSubmit={submit} className="space-y-3 pt-3">
                        <input type="password" value={cur} onChange={e => setCur(e.target.value)} required placeholder="Current password"
                          className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-300" />
                        <input type="password" value={nw} onChange={e => setNw(e.target.value)} required placeholder="New password" minLength={8}
                          className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-300" />
                        <input type="password" value={cf} onChange={e => setCf(e.target.value)} required placeholder="Confirm new password"
                          className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-300" />
                        {err && <p className="text-xs text-red-500">{err}</p>}
                        <div className="flex gap-2">
                          <button type="button" onClick={onDone} className="flex-1 py-2 rounded-lg border border-gray-200 text-sm text-gray-600 hover:bg-gray-50">Cancel</button>
                          <button type="submit" disabled={saving} className="flex-1 py-2 rounded-lg bg-gray-900 text-white text-sm font-semibold hover:bg-gray-700 disabled:opacity-40">
                            {saving ? 'Saving…' : 'Update Password'}
                          </button>
                        </div>
                      </form>
                    )
                  }}
                />
              </div>
            </div>

            {/* Account info */}
            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm">
              <div className="px-6 py-4 border-b border-gray-100">
                <p className="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">Account Info</p>
              </div>
              <div className="divide-y divide-gray-100 px-6">
                <InfoRow label="User ID" value={`#${user?.id}`} />
                <InfoRow label="Member since" value={user?.created_at ? new Date(user.created_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' }) : '—'} />
                <InfoRow label="Email verified" value={user?.verified ? '✓ Verified' : '✗ Not verified'} valueClass={user?.verified ? 'text-green-600' : 'text-orange-500'} />
                <InfoRow label="Total lookups" value={user?.total_lookups ?? 0} />
                <div className="flex items-center justify-between py-4">
                  <div>
                    <p className="text-sm text-gray-500">Balance</p>
                    <p className="text-sm font-semibold text-gray-800">{fmtEUR(user?.balance_eur || 0)}</p>
                  </div>
                  <button onClick={() => setShowTopUp(true)} className="text-sm text-gray-700 border border-gray-200 px-3 py-1.5 rounded-lg hover:bg-gray-50 font-medium">
                    Add Funds
                  </button>
                </div>
              </div>
            </div>

            {/* Telegram */}
            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm">
              <div className="px-6 py-4 border-b border-gray-100">
                <p className="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">Telegram</p>
              </div>
              <div className="px-6 py-4 flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-800">{user?.telegram_linked ? 'Connected' : 'Not connected'}</p>
                  <p className="text-xs text-gray-400 mt-0.5">
                    {user?.telegram_linked ? 'Your Telegram shares this balance.' : 'Link to use the bot with this account.'}
                  </p>
                </div>
                {user?.telegram_linked ? (
                  <button onClick={unlinkTelegram} className="text-sm text-red-500 border border-red-200 px-3 py-1.5 rounded-lg hover:bg-red-50">
                    Disconnect
                  </button>
                ) : (
                  <button onClick={() => setActiveNav('home')} className="text-sm text-gray-700 border border-gray-200 px-3 py-1.5 rounded-lg hover:bg-gray-50">
                    Link Account
                  </button>
                )}
              </div>
            </div>

            {/* Authenticator App (TOTP) */}
            <TotpSection user={user} refreshUser={refreshUser} />

            {/* Theme Settings */}
            <ThemeSettings />

            {/* Sign out */}
            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm">
              <div className="px-6 py-4 border-b border-gray-100">
                <p className="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">Session</p>
              </div>
              <div className="px-6 py-4">
                <button onClick={signout} className="flex items-center gap-2 text-sm text-red-600 border border-red-200 px-4 py-2 rounded-lg hover:bg-red-50 transition-colors font-medium">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/></svg>
                  Sign Out
                </button>
              </div>
            </div>

          </div>
        )}

      </main>

      {/* Telegram floating button */}
      <a
        href="https://t.me/AppleConfigBot"
        target="_blank"
        rel="noopener noreferrer"
        className="fixed bottom-6 right-6 z-50 flex items-center gap-2 bg-[#229ED9] hover:bg-[#1a8bbf] text-white px-4 py-3 rounded-full shadow-lg transition-colors"
        title="Open Telegram Bot"
      >
        <svg className="w-5 h-5 shrink-0" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.894 8.221-1.97 9.28c-.145.658-.537.818-1.084.508l-3-2.21-1.447 1.394c-.16.16-.295.295-.605.295l.213-3.053 5.56-5.023c.242-.213-.054-.333-.373-.12L8.32 14.617l-2.96-.924c-.643-.204-.657-.643.136-.953l11.57-4.461c.537-.194 1.006.131.828.942z"/>
        </svg>
        <span className="text-sm font-semibold">Telegram Bot</span>
      </a>
    </div>
  )
}
