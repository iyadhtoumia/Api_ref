import React, { useEffect, useState } from 'react'
import axios from '../../utils/axios'

function StatCard({ label, value, sub }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
      <p className="text-xs font-medium text-gray-400 uppercase tracking-wider">{label}</p>
      <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
      {sub && <p className="text-xs text-gray-400 mt-0.5">{sub}</p>}
    </div>
  )
}

const fmtEUR = (cents) => `€${(cents / 100).toFixed(2)}`

export default function AdminDashboard() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    axios.get('/api/admin/stats')
      .then(r => setStats(r.data))
      .catch(() => setError('Failed to load stats'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="p-8 text-gray-400 text-sm">Loading…</div>
  if (error)   return <div className="p-8 text-red-500 text-sm">{error}</div>

  return (
    <div className="p-8 space-y-8">
      <h1 className="text-xl font-semibold text-gray-900">Dashboard</h1>

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
        <StatCard label="Total Users"     value={stats.total_users}               sub={`+${stats.new_users_today} today`} />
        <StatCard label="Total Revenue"   value={fmtEUR(stats.total_revenue)}     sub={`${fmtEUR(stats.revenue_today)} today`} />
        <StatCard label="Total Lookups"   value={stats.total_lookups.toLocaleString()} sub={`${stats.lookups_today} today`} />
      </div>

      {/* Top services table */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
        <div className="px-5 py-4 border-b border-gray-100">
          <h2 className="text-sm font-semibold text-gray-700">Top 5 Services by Usage</h2>
        </div>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-xs text-gray-400 uppercase tracking-wider border-b border-gray-100">
              <th className="text-left px-5 py-3">Service</th>
              <th className="text-right px-5 py-3">Uses</th>
              <th className="text-right px-5 py-3">Revenue</th>
            </tr>
          </thead>
          <tbody>
            {stats.top_services.length === 0 && (
              <tr><td colSpan={3} className="px-5 py-6 text-center text-gray-400">No data yet</td></tr>
            )}
            {stats.top_services.map((s, i) => (
              <tr key={i} className="border-b border-gray-50 last:border-0 hover:bg-gray-50">
                <td className="px-5 py-3 text-gray-800 font-medium">{s.service_name}</td>
                <td className="px-5 py-3 text-right text-gray-600 tabular-nums">{s.uses}</td>
                <td className="px-5 py-3 text-right text-gray-600 tabular-nums">{fmtEUR(s.revenue)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
