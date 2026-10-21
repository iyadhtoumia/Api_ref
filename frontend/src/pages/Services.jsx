import React, { useState, useEffect, useMemo } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import axios from '../utils/axios'
import { useAuth } from '../context/AuthContext'

const CATEGORY_ORDER = [
  'Apple Check Services',
  'Premium Tools & Services',
  'Status Check Services',
  'Generic Services',
  'iPhone Unlock Services',
  'Generic Unlock Services',
]

// ── Inline lookup modal ───────────────────────────────────────────────────────
function LookupModal({ service, onClose, onDone }) {
  const [serial, setSerial] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (serial.length < 4) { setError('Serial too short'); return }
    setError(''); setResult(null); setLoading(true)
    try {
      const res = await axios.post('/api/lookup-config', { serial: serial.trim().toUpperCase(), service_id: service.id })
      setResult(res.data)
      onDone?.()
    } catch (err) {
      setError(err.response?.data?.error || 'Lookup failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="font-semibold text-gray-900">{service.name}</h2>
            <p className="text-xs text-gray-400 mt-0.5">Cost: €{service.price.toFixed(3)}</p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12"/></svg>
          </button>
        </div>

        {!result ? (
          <form onSubmit={handleSubmit} className="space-y-3">
            <input
              type="text"
              value={serial}
              onChange={e => setSerial(e.target.value.toUpperCase())}
              placeholder="Enter IMEI or serial number"
              className="w-full border border-gray-200 rounded-lg px-4 py-2.5 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-gray-300"
              minLength={4} maxLength={20} required
            />
            {error && <p className="text-sm text-red-600">{error}</p>}
            <button type="submit" disabled={loading}
              className="w-full bg-gray-900 text-white py-2.5 rounded-lg text-sm font-semibold hover:bg-gray-700 disabled:opacity-50 flex items-center justify-center gap-2">
              {loading
                ? <><span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"/>Checking…</>
                : 'Run Check'}
            </button>
          </form>
        ) : (
          <div className="space-y-3">
            <div className="p-4 bg-green-50 border border-green-200 rounded-lg text-sm">
              <p className="font-mono font-semibold text-gray-800 mb-1">{result.serial}</p>
              <p className="text-gray-700 whitespace-pre-wrap">{result.config}</p>
            </div>
            <div className="flex gap-2">
              <button onClick={() => { setResult(null); setSerial('') }}
                className="flex-1 py-2 text-sm rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50">
                New Check
              </button>
              <button onClick={onClose}
                className="flex-1 py-2 text-sm rounded-lg bg-gray-900 text-white font-semibold hover:bg-gray-700">
                Done
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}



export default function Services() {
  const { user } = useAuth()
  const [services, setServices]     = useState([])
  const [loading, setLoading]       = useState(true)
  const [search, setSearch]         = useState('')
  const [activeCategory, setActiveCategory] = useState('All')
  const [selectedService, setSelectedService] = useState(null)

  useEffect(() => {
    axios.get('/api/services')
      .then(r => setServices(r.data.services || []))
      .catch(() => setServices([]))
      .finally(() => setLoading(false))
  }, [])

  // Filter by search + category
  const filtered = useMemo(() => {
    const q = search.toLowerCase()
    return services.filter(s => {
      const matchSearch = !q ||
        s.name.toLowerCase().includes(q) ||
        String(s.id).includes(q)
      const matchCat = activeCategory === 'All' || s.category === activeCategory
      return matchSearch && matchCat
    })
  }, [services, search, activeCategory])

  // Group filtered by category, preserving order
  const grouped = useMemo(() => {
    const map = {}
    for (const s of filtered) {
      if (!map[s.category]) map[s.category] = []
      map[s.category].push(s)
    }
    // Sort categories by defined order, unknowns at end
    return Object.entries(map).sort(([a], [b]) => {
      const ia = CATEGORY_ORDER.indexOf(a)
      const ib = CATEGORY_ORDER.indexOf(b)
      return (ia === -1 ? 99 : ia) - (ib === -1 ? 99 : ib)
    })
  }, [filtered])

  const categories = ['All', ...CATEGORY_ORDER.filter(c =>
    services.some(s => s.category === c)
  )]

  const totalActive = services.length

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 text-gray-800 dark:text-gray-100">

      {selectedService && (
        <LookupModal
          service={selectedService}
          onClose={() => setSelectedService(null)}
          onDone={() => setSelectedService(null)}
        />
      )}

      {/* Navbar */}
      <nav className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 flex items-center gap-4 h-14">
          <Link to="/" className="text-sm font-semibold text-gray-900">
            IMEI Check
          </Link>
          <div className="flex-1" />
          <Link to="/services" className="text-sm font-medium text-gray-900 border-b-2 border-gray-900 pb-0.5">
            Services & Prices
          </Link>
          {user ? (
            <Link to="/dashboard"
              className="text-sm bg-gray-900 text-white px-4 py-1.5 rounded-lg font-medium hover:bg-gray-700">
              Dashboard
            </Link>
          ) : (
            <div className="flex items-center gap-2">
              <Link to="/signin" className="text-sm text-gray-600 hover:text-gray-900">Sign In</Link>
              <Link to="/signup"
                className="text-sm bg-gray-900 text-white px-4 py-1.5 rounded-lg font-medium hover:bg-gray-700">
                Sign Up
              </Link>
            </div>
          )}
        </div>
      </nav>

      <main className="max-w-5xl mx-auto px-4 py-10">

        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Services & Prices</h1>
          <p className="text-gray-500 text-sm">
            {totalActive} services available — use the service ID when making API calls
          </p>
        </div>

        {/* Search + category filter */}
        <div className="bg-white rounded-xl border border-gray-200 p-4 mb-6 shadow-sm space-y-3">
          <div className="relative">
            <svg className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
              fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              type="text"
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Search by service name or ID…"
              className="w-full pl-9 pr-4 py-2.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-300"
            />
          </div>

          {/* Category pills */}
          <div className="flex flex-wrap gap-2">
            {categories.map(cat => (
              <button
                key={cat}
                onClick={() => setActiveCategory(cat)}
                className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
                  activeCategory === cat
                    ? 'bg-gray-900 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
              {cat !== 'All' ? cat : 'All'}
              </button>
            ))}
          </div>
        </div>

        {/* Results count */}
        {search && (
          <p className="text-sm text-gray-500 mb-4">
            {filtered.length} result{filtered.length !== 1 ? 's' : ''} for "{search}"
          </p>
        )}

        {/* Loading */}
        {loading && (
          <div className="text-center py-16 text-gray-400 text-sm">Loading services…</div>
        )}

        {/* Empty */}
        {!loading && filtered.length === 0 && (
          <div className="text-center py-16 text-gray-400 text-sm">No services found.</div>
        )}

        {/* Service groups */}
        {!loading && grouped.map(([category, items]) => (
          <div key={category} className="mb-8">
            {/* Category header */}
            <div className="flex items-center gap-2 mb-3">
              <h2 className="text-sm font-semibold text-gray-900 uppercase tracking-wider">{category}</h2>
              <span className="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full">{items.length}</span>
            </div>

            <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
              {items.map((svc, idx) => (
                <div
                  key={svc.id}
                  className={`flex items-center gap-4 px-4 py-3 ${
                    idx !== items.length - 1 ? 'border-b border-gray-100' : ''
                  }`}
                >
                  {/* ID badge */}
                  <span className="text-xs font-mono bg-gray-100 text-gray-500 px-2 py-1 rounded shrink-0 w-12 text-center">
                    {svc.id}
                  </span>

                  {/* Name */}
                  <span className="text-sm text-gray-800 flex-1">{svc.name}</span>

                  {/* Price */}
                  <span className={`text-sm font-semibold shrink-0 ${
                    svc.price === 0 ? 'text-green-600' : 'text-gray-900'
                  }`}>
                    {svc.price === 0 ? 'FREE' : `€${svc.price.toFixed(3)}`}
                  </span>

                  {/* Check button — only for logged-in users */}
                  {user && (
                    <button
                      onClick={() => setSelectedService(svc)}
                      className="shrink-0 text-xs font-semibold px-3 py-1.5 rounded-lg bg-gray-900 text-white hover:bg-gray-700 transition-colors"
                    >
                      Check
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        ))}

        {/* CTA */}
        {!loading && !user && (
          <div className="mt-10 bg-gray-900 rounded-xl p-8 text-center text-white">
            <h3 className="text-lg font-semibold mb-2">Ready to start checking?</h3>
            <p className="text-gray-400 text-sm mb-6">Create an account and run your first check in minutes.</p>
            <Link to="/signup"
              className="bg-white text-gray-900 px-6 py-2.5 rounded-lg font-semibold text-sm hover:bg-gray-100">
              Create Account
            </Link>
          </div>
        )}
      </main>

      {/* Telegram button */}
      <a href="https://t.me/AppleConfigBot" target="_blank" rel="noopener noreferrer"
        className="fixed bottom-6 right-6 z-50 flex items-center gap-2 bg-[#229ED9] hover:bg-[#1a8bbf] text-white px-4 py-3 rounded-full shadow-lg transition-colors">
        <svg className="w-5 h-5 shrink-0" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.894 8.221-1.97 9.28c-.145.658-.537.818-1.084.508l-3-2.21-1.447 1.394c-.16.16-.295.295-.605.295l.213-3.053 5.56-5.023c.242-.213-.054-.333-.373-.12L8.32 14.617l-2.96-.924c-.643-.204-.657-.643.136-.953l11.57-4.461c.537-.194 1.006.131.828.942z"/>
        </svg>
        <span className="text-sm font-semibold">Telegram Bot</span>
      </a>
    </div>
  )
}
