import React, { useEffect, useState, useCallback } from 'react'
import axios from '../../utils/axios'

const fmtEUR  = (cents) => `€${(cents / 100).toFixed(2)}`
const fmtDate = (d) => d ? new Date(d).toLocaleString() : '—'

const STATUS_COLORS = {
  paid:      'bg-green-100 text-green-700',
  pending:   'bg-yellow-100 text-yellow-700',
  refunded:  'bg-gray-100 text-gray-500',
  completed: 'bg-blue-100 text-blue-700',
}

export default function AdminTransactions() {
  const [rows, setRows]       = useState([])
  const [total, setTotal]     = useState(0)
  const [pages, setPages]     = useState(1)
  const [page, setPage]       = useState(1)
  const [type, setType]       = useState('')     // '' | 'payment' | 'lookup'
  const [status, setStatus]   = useState('')     // '' | 'paid' | 'pending' | 'refunded'
  const [search, setSearch]   = useState('')
  const [loading, setLoading] = useState(true)
  const [refunding, setRefunding] = useState(null)

  const load = useCallback(async (p = 1) => {
    setLoading(true)
    try {
      const res = await axios.get('/api/admin/transactions', {
        params: { page: p, type, status, search }
      })
      setRows(res.data.transactions)
      setTotal(res.data.total)
      setPages(res.data.pages)
    } catch { /* ignore */ }
    finally { setLoading(false) }
  }, [type, status, search]) // eslint-disable-line

  useEffect(() => {
    setPage(1)
    load(1)
  }, [type, status]) // eslint-disable-line

  useEffect(() => { load(page) }, [page]) // eslint-disable-line

  const handleSearch = (e) => {
    e.preventDefault()
    setPage(1)
    load(1)
  }

  const handleRefund = async (row) => {
    setRefunding(row.id)
    try {
      await axios.post(`/api/admin/transactions/refund/${row.id}`)
      setRows(prev => prev.map(r => r.id === row.id && r.type === 'payment'
        ? { ...r, status: 'refunded' } : r))
    } catch (err) {
      alert(err.response?.data?.error || 'Refund failed')
    } finally {
      setRefunding(null)
    }
  }

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h1 className="text-xl font-semibold text-gray-900">
          Transactions <span className="text-sm font-normal text-gray-400">({total})</span>
        </h1>

        {/* Filters */}
        <div className="flex flex-wrap gap-2 items-center">
          {/* Type filter */}
          <div className="flex gap-1 p-1 bg-gray-100 rounded-lg text-sm">
            {[['', 'All'], ['payment', 'Payments'], ['lookup', 'Lookups']].map(([v, l]) => (
              <button key={v} onClick={() => setType(v)}
                className={`px-3 py-1 rounded-md font-medium transition-colors ${type === v ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}>
                {l}
              </button>
            ))}
          </div>

          {/* Status filter (only relevant for payments) */}
          {(type === '' || type === 'payment') && (
            <select value={status} onChange={e => setStatus(e.target.value)}
              className="border border-gray-200 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-gray-300">
              <option value="">All statuses</option>
              <option value="paid">Paid</option>
              <option value="pending">Pending</option>
              <option value="refunded">Refunded</option>
            </select>
          )}

          {/* Search */}
          <form onSubmit={handleSearch} className="flex gap-2">
            <input value={search} onChange={e => setSearch(e.target.value)}
              placeholder="Email or serial…"
              className="border border-gray-200 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-gray-300 w-48" />
            <button type="submit"
              className="px-3 py-1.5 bg-gray-900 text-white text-sm rounded-lg hover:bg-gray-700">Search</button>
          </form>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-xs text-gray-400 uppercase tracking-wider border-b border-gray-100 bg-gray-50">
              <th className="text-left px-4 py-3">ID</th>
              <th className="text-left px-4 py-3">User</th>
              <th className="text-center px-4 py-3">Type</th>
              <th className="text-left px-4 py-3">Detail</th>
              <th className="text-right px-4 py-3">Amount</th>
              <th className="text-center px-4 py-3">Status</th>
              <th className="text-left px-4 py-3">Date</th>
              <th className="text-right px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr><td colSpan={8} className="px-4 py-8 text-center text-gray-400">Loading…</td></tr>
            )}
            {!loading && rows.length === 0 && (
              <tr><td colSpan={8} className="px-4 py-8 text-center text-gray-400">No transactions found</td></tr>
            )}
            {!loading && rows.map((row, i) => (
              <tr key={`${row.type}-${row.id}-${i}`} className="border-b border-gray-50 last:border-0 hover:bg-gray-50">
                <td className="px-4 py-3 font-mono text-xs text-gray-400">#{row.id}</td>
                <td className="px-4 py-3 text-gray-700 text-xs truncate max-w-[140px]">{row.email}</td>
                <td className="px-4 py-3 text-center">
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                    row.type === 'payment' ? 'bg-purple-100 text-purple-700' : 'bg-blue-100 text-blue-700'
                  }`}>
                    {row.type}
                  </span>
                </td>
                <td className="px-4 py-3 text-gray-500 text-xs">
                  {row.type === 'payment'
                    ? (row.provider || 'stripe')
                    : <span title={row.serial}>{row.service_name || '—'}</span>}
                </td>
                <td className="px-4 py-3 text-right tabular-nums font-medium text-gray-800">
                  {fmtEUR(row.amount_eur)}
                </td>
                <td className="px-4 py-3 text-center">
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_COLORS[row.status] || 'bg-gray-100 text-gray-500'}`}>
                    {row.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-gray-400 text-xs">{fmtDate(row.created_at)}</td>
                <td className="px-4 py-3 text-right">
                  {row.type === 'payment' && row.status === 'paid' && (
                    <button
                      disabled={refunding === row.id}
                      onClick={() => handleRefund(row)}
                      className="text-xs text-orange-500 hover:text-orange-700 font-medium disabled:opacity-40">
                      {refunding === row.id ? 'Refunding…' : 'Refund'}
                    </button>
                  )}
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
