import React, { useEffect, useState, useCallback } from 'react'
import axios from '../../utils/axios'

const fmtEUR  = (cents) => `€${(cents / 100).toFixed(2)}`
const fmtDate = (d) => d ? new Date(d).toLocaleDateString() : '—'

function EditBalanceModal({ user, onClose, onSaved }) {
  const [mode, setMode] = useState('add')   // 'add' | 'set'
  const [amount, setAmount] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError]   = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    const cents = Math.round(parseFloat(amount) * 100)
    if (isNaN(cents)) { setError('Enter a valid amount'); return }
    setSaving(true)
    try {
      const payload = mode === 'add' ? { add_balance: cents } : { balance_eur: cents }
      const res = await axios.patch(`/api/admin/users/${user.id}`, payload)
      onSaved(res.data.user)
    } catch (err) {
      setError(err.response?.data?.error || 'Failed')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-sm p-6">
        <h2 className="font-semibold text-gray-900 mb-1">Adjust Balance</h2>
        <p className="text-xs text-gray-400 mb-4">{user.email} — current: {fmtEUR(user.balance_eur)}</p>
        <div className="flex gap-2 mb-4">
          {['add', 'set'].map(m => (
            <button key={m} onClick={() => setMode(m)}
              className={`flex-1 py-1.5 rounded-lg text-sm font-semibold border transition-colors ${mode === m ? 'bg-gray-900 text-white border-gray-900' : 'border-gray-200 text-gray-600'}`}>
              {m === 'add' ? 'Add' : 'Set to'}
            </button>
          ))}
        </div>
        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="relative">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">€</span>
            <input type="number" step="0.01" min="0" value={amount} onChange={e => setAmount(e.target.value)}
              className="w-full pl-7 pr-4 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-300"
              placeholder="0.00" required />
          </div>
          {error && <p className="text-xs text-red-500">{error}</p>}
          <div className="flex gap-2 pt-1">
            <button type="button" onClick={onClose}
              className="flex-1 py-2 rounded-lg border border-gray-200 text-sm text-gray-600 hover:bg-gray-50">Cancel</button>
            <button type="submit" disabled={saving}
              className="flex-1 py-2 rounded-lg bg-gray-900 text-white text-sm font-semibold hover:bg-gray-700 disabled:opacity-40">
              {saving ? 'Saving…' : 'Confirm'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function AdminUsers() {
  const [users, setUsers]     = useState([])
  const [total, setTotal]     = useState(0)
  const [pages, setPages]     = useState(1)
  const [page, setPage]       = useState(1)
  const [search, setSearch]   = useState('')
  const [loading, setLoading] = useState(true)
  const [editing, setEditing] = useState(null)   // user being balance-edited
  const [confirm, setConfirm] = useState(null)   // { type: 'ban'|'unban'|'delete', user }

  const load = useCallback(async (p = 1, q = '') => {
    setLoading(true)
    try {
      const res = await axios.get('/api/admin/users', { params: { page: p, search: q } })
      setUsers(res.data.users)
      setTotal(res.data.total)
      setPages(res.data.pages)
    } catch { /* ignore */ }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { load(page, search) }, [page]) // eslint-disable-line

  const handleSearch = (e) => {
    e.preventDefault()
    setPage(1)
    load(1, search)
  }

  const applyPatch = async (id, payload) => {
    const res = await axios.patch(`/api/admin/users/${id}`, payload)
    setUsers(prev => prev.map(u => u.id === id ? res.data.user : u))
  }

  const handleDelete = async (id) => {
    await axios.delete(`/api/admin/users/${id}`)
    setUsers(prev => prev.filter(u => u.id !== id))
    setTotal(t => t - 1)
  }

  const handleConfirm = async () => {
    const { type, user } = confirm
    setConfirm(null)
    if (type === 'ban')    await applyPatch(user.id, { banned: true })
    if (type === 'unban')  await applyPatch(user.id, { banned: false })
    if (type === 'verify') await applyPatch(user.id, { verified: true })
    if (type === 'delete') await handleDelete(user.id)
  }

  return (
    <div className="p-8 space-y-6">
      {editing && (
        <EditBalanceModal
          user={editing}
          onClose={() => setEditing(null)}
          onSaved={(updated) => {
            setUsers(prev => prev.map(u => u.id === updated.id ? updated : u))
            setEditing(null)
          }}
        />
      )}

      {confirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-sm p-6 text-center">
            <p className="text-sm text-gray-700 mb-4">
              {confirm.type === 'delete' && <><strong>Delete</strong> {confirm.user.email}? This is irreversible.</>}
              {confirm.type === 'ban'    && <>Ban <strong>{confirm.user.email}</strong>?</>}
              {confirm.type === 'unban'  && <>Unban <strong>{confirm.user.email}</strong>?</>}
              {confirm.type === 'verify' && <>Manually verify <strong>{confirm.user.email}</strong>?</>}
            </p>
            <div className="flex gap-2 justify-center">
              <button onClick={() => setConfirm(null)}
                className="px-5 py-2 rounded-lg border border-gray-200 text-sm text-gray-600 hover:bg-gray-50">Cancel</button>
              <button onClick={handleConfirm}
                className={`px-5 py-2 rounded-lg text-sm font-semibold text-white ${confirm.type === 'delete' || confirm.type === 'ban' ? 'bg-red-600 hover:bg-red-700' : 'bg-gray-900 hover:bg-gray-700'}`}>
                Confirm
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="flex items-center justify-between flex-wrap gap-3">
        <h1 className="text-xl font-semibold text-gray-900">Users <span className="text-sm font-normal text-gray-400">({total})</span></h1>
        <form onSubmit={handleSearch} className="flex gap-2">
          <input value={search} onChange={e => setSearch(e.target.value)}
            placeholder="Search email…"
            className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-300 w-56" />
          <button type="submit" className="px-4 py-2 bg-gray-900 text-white text-sm rounded-lg hover:bg-gray-700">Search</button>
        </form>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-xs text-gray-400 uppercase tracking-wider border-b border-gray-100 bg-gray-50">
              <th className="text-left px-4 py-3">Email</th>
              <th className="text-right px-4 py-3">Balance</th>
              <th className="text-right px-4 py-3">Lookups</th>
              <th className="text-center px-4 py-3">Verified</th>
              <th className="text-center px-4 py-3">Status</th>
              <th className="text-left px-4 py-3">Joined</th>
              <th className="text-right px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-400">Loading…</td></tr>
            )}
            {!loading && users.length === 0 && (
              <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-400">No users found</td></tr>
            )}
            {!loading && users.map(u => (
              <tr key={u.id} className={`border-b border-gray-50 last:border-0 hover:bg-gray-50 ${u.banned ? 'opacity-60' : ''}`}>
                <td className="px-4 py-3 font-medium text-gray-800">{u.email}</td>
                <td className="px-4 py-3 text-right tabular-nums text-gray-700">{fmtEUR(u.balance_eur)}</td>
                <td className="px-4 py-3 text-right tabular-nums text-gray-500">{u.total_lookups}</td>
                <td className="px-4 py-3 text-center">
                  {u.verified
                    ? <span className="text-green-600 text-xs font-medium">Yes</span>
                    : <button onClick={() => setConfirm({ type: 'verify', user: u })}
                        className="text-xs text-orange-500 underline hover:text-orange-700">Verify</button>}
                </td>
                <td className="px-4 py-3 text-center">
                  {u.banned
                    ? <span className="bg-red-100 text-red-600 text-xs px-2 py-0.5 rounded-full">Banned</span>
                    : <span className="bg-green-100 text-green-700 text-xs px-2 py-0.5 rounded-full">Active</span>}
                </td>
                <td className="px-4 py-3 text-gray-400 text-xs">{fmtDate(u.created_at)}</td>
                <td className="px-4 py-3 text-right">
                  <div className="flex items-center justify-end gap-2">
                    <button onClick={() => setEditing(u)}
                      className="text-xs text-blue-600 hover:text-blue-800 font-medium">Balance</button>
                    {u.banned
                      ? <button onClick={() => setConfirm({ type: 'unban', user: u })}
                          className="text-xs text-green-600 hover:text-green-800 font-medium">Unban</button>
                      : <button onClick={() => setConfirm({ type: 'ban', user: u })}
                          className="text-xs text-orange-500 hover:text-orange-700 font-medium">Ban</button>}
                    <button onClick={() => setConfirm({ type: 'delete', user: u })}
                      className="text-xs text-red-500 hover:text-red-700 font-medium">Delete</button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {pages > 1 && (
        <div className="flex items-center gap-2 justify-end text-sm">
          <button disabled={page === 1} onClick={() => setPage(p => p - 1)}
            className="px-3 py-1.5 rounded-lg border border-gray-200 text-gray-600 disabled:opacity-40 hover:bg-gray-50">← Prev</button>
          <span className="text-gray-400 text-xs">Page {page} of {pages}</span>
          <button disabled={page === pages} onClick={() => setPage(p => p + 1)}
            className="px-3 py-1.5 rounded-lg border border-gray-200 text-gray-600 disabled:opacity-40 hover:bg-gray-50">Next →</button>
        </div>
      )}
    </div>
  )
}
