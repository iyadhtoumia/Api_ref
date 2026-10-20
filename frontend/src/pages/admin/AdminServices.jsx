import React, { useEffect, useState, useCallback } from 'react'
import axios from '../../utils/axios'

const BLANK = { id: '', name: '', category: '', price: '' }

function ServiceForm({ initial, onSave, onCancel }) {
  const [form, setForm] = useState(initial || BLANK)
  const [saving, setSaving] = useState(false)
  const [error, setError]   = useState('')
  const isNew = !initial

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    try {
      const payload = { ...form, price: parseFloat(form.price) }
      if (isNew) payload.id = parseInt(form.id)
      const res = isNew
        ? await axios.post('/api/admin/services', payload)
        : await axios.patch(`/api/admin/services/${initial.id}`, payload)
      onSave(res.data)
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to save')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-6">
        <h2 className="font-semibold text-gray-900 mb-4">{isNew ? 'Add Service' : `Edit Service #${initial.id}`}</h2>
        <form onSubmit={handleSubmit} className="space-y-3">
          {isNew && (
            <div>
              <label className="text-xs text-gray-500 mb-1 block">Sickw Service ID</label>
              <input type="number" value={form.id} onChange={e => set('id', e.target.value)}
                required className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-300" />
            </div>
          )}
          <div>
            <label className="text-xs text-gray-500 mb-1 block">Name</label>
            <input value={form.name} onChange={e => set('name', e.target.value)}
              required className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-300" />
          </div>
          <div>
            <label className="text-xs text-gray-500 mb-1 block">Category</label>
            <input value={form.category} onChange={e => set('category', e.target.value)}
              required className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-300" />
          </div>
          <div>
            <label className="text-xs text-gray-500 mb-1 block">Price (€)</label>
            <input type="number" step="0.001" min="0" value={form.price} onChange={e => set('price', e.target.value)}
              required className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-300" />
          </div>
          {error && <p className="text-xs text-red-500">{error}</p>}
          <div className="flex gap-2 pt-1">
            <button type="button" onClick={onCancel}
              className="flex-1 py-2 rounded-lg border border-gray-200 text-sm text-gray-600 hover:bg-gray-50">Cancel</button>
            <button type="submit" disabled={saving}
              className="flex-1 py-2 rounded-lg bg-gray-900 text-white text-sm font-semibold hover:bg-gray-700 disabled:opacity-40">
              {saving ? 'Saving…' : 'Save'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function AdminServices() {
  const [services, setServices] = useState([])
  const [loading, setLoading]   = useState(true)
  const [search, setSearch]     = useState('')
  const [editing, setEditing]   = useState(null)   // service object or 'new'
  const [confirm, setConfirm]   = useState(null)   // service to delete

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const res = await axios.get('/api/admin/services')
      setServices(res.data.services)
    } catch { /* ignore */ }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { load() }, [load])

  const filtered = services.filter(s =>
    !search ||
    s.name.toLowerCase().includes(search.toLowerCase()) ||
    String(s.id).includes(search) ||
    s.category.toLowerCase().includes(search.toLowerCase())
  )

  const handleToggleActive = async (svc) => {
    const res = await axios.patch(`/api/admin/services/${svc.id}`, { active: !svc.active })
    setServices(prev => prev.map(s => s.id === svc.id ? res.data.service : s))
  }

  const handleDelete = async () => {
    await axios.delete(`/api/admin/services/${confirm.id}`)
    setServices(prev => prev.filter(s => s.id !== confirm.id))
    setConfirm(null)
  }

  const handleSaved = (data) => {
    if (editing === 'new') {
      load()
    } else {
      setServices(prev => prev.map(s => s.id === data.service?.id ? data.service : s))
    }
    setEditing(null)
  }

  return (
    <div className="p-8 space-y-6">
      {editing && (
        <ServiceForm
          initial={editing === 'new' ? null : editing}
          onSave={handleSaved}
          onCancel={() => setEditing(null)}
        />
      )}

      {confirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-sm p-6 text-center">
            <p className="text-sm text-gray-700 mb-4">Delete <strong>{confirm.name}</strong>?</p>
            <div className="flex gap-2 justify-center">
              <button onClick={() => setConfirm(null)}
                className="px-5 py-2 rounded-lg border border-gray-200 text-sm text-gray-600 hover:bg-gray-50">Cancel</button>
              <button onClick={handleDelete}
                className="px-5 py-2 rounded-lg bg-red-600 text-white text-sm font-semibold hover:bg-red-700">Delete</button>
            </div>
          </div>
        </div>
      )}

      <div className="flex items-center justify-between flex-wrap gap-3">
        <h1 className="text-xl font-semibold text-gray-900">
          Services <span className="text-sm font-normal text-gray-400">({filtered.length})</span>
        </h1>
        <div className="flex gap-2">
          <input value={search} onChange={e => setSearch(e.target.value)}
            placeholder="Filter by name, ID, category…"
            className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-300 w-64" />
          <button onClick={() => setEditing('new')}
            className="px-4 py-2 bg-gray-900 text-white text-sm rounded-lg hover:bg-gray-700 font-semibold">
            + Add
          </button>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-xs text-gray-400 uppercase tracking-wider border-b border-gray-100 bg-gray-50">
              <th className="text-left px-4 py-3 w-16">ID</th>
              <th className="text-left px-4 py-3">Name</th>
              <th className="text-left px-4 py-3">Category</th>
              <th className="text-right px-4 py-3">Price</th>
              <th className="text-center px-4 py-3">Status</th>
              <th className="text-left px-4 py-3">Last Check</th>
              <th className="text-right px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-400">Loading…</td></tr>
            )}
            {!loading && filtered.length === 0 && (
              <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-400">No services found</td></tr>
            )}
            {!loading && filtered.map(s => (
              <tr key={s.id} className={`border-b border-gray-50 last:border-0 hover:bg-gray-50 ${!s.active ? 'opacity-50' : ''}`}>
                <td className="px-4 py-3 font-mono text-xs text-gray-500">{s.id}</td>
                <td className="px-4 py-3 font-medium text-gray-800">{s.name}</td>
                <td className="px-4 py-3 text-gray-500 text-xs">{s.category}</td>
                <td className="px-4 py-3 text-right tabular-nums text-gray-700">€{Number(s.price).toFixed(3)}</td>
                <td className="px-4 py-3 text-center">
                  <button onClick={() => handleToggleActive(s)}
                    className={`text-xs px-2 py-0.5 rounded-full font-medium transition-colors ${
                      s.active
                        ? 'bg-green-100 text-green-700 hover:bg-green-200'
                        : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
                    }`}>
                    {s.active ? 'Active' : 'Inactive'}
                  </button>
                </td>
                <td className="px-4 py-3 text-xs text-gray-400">
                  {s.last_checked ? new Date(s.last_checked).toLocaleString() : '—'}
                  {s.last_status && s.last_status !== 'unknown' &&
                    <span className={`ml-1 ${s.last_status === 'ok' ? 'text-green-500' : 'text-red-400'}`}>
                      ({s.last_status})
                    </span>}
                </td>
                <td className="px-4 py-3 text-right">
                  <div className="flex items-center justify-end gap-2">
                    <button onClick={() => setEditing(s)}
                      className="text-xs text-blue-600 hover:text-blue-800 font-medium">Edit</button>
                    <button onClick={() => setConfirm(s)}
                      className="text-xs text-red-500 hover:text-red-700 font-medium">Delete</button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
