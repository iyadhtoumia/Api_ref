import React, { useEffect, useState } from 'react'
import axios from '../../utils/axios'

function StatCard({ label, value, sub }) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5 shadow-sm">
      <p className="text-xs font-medium text-gray-400 dark:text-gray-500 uppercase tracking-wider">{label}</p>
      <p className="text-2xl font-bold text-gray-900 dark:text-gray-100 mt-1">{value}</p>
      {sub && <p className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">{sub}</p>}
    </div>
  )
}

function GoogleAnalyticsDashboard() {
  const gaPropertyId = import.meta.env.VITE_GA_MEASUREMENT_ID
  
  if (!gaPropertyId || gaPropertyId === 'G-XXXXXXXXXX') {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-8 text-center">
        <div className="text-gray-400 mb-4">
          <svg className="w-16 h-16 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          <h3 className="text-lg font-semibold text-gray-600 mb-2">Google Analytics Not Configured</h3>
          <p className="text-sm text-gray-500 max-w-md mx-auto">
            Set your Google Analytics Measurement ID in the <code className="bg-gray-100 px-2 py-1 rounded">.env</code> file to see analytics data here.
          </p>
          <a 
            href="https://analytics.google.com" 
            target="_blank" 
            rel="noopener noreferrer"
            className="inline-block mt-4 text-blue-600 hover:text-blue-700 text-sm font-medium"
          >
            Get started with Google Analytics →
          </a>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Quick Links */}
      <div className="flex gap-3 flex-wrap">
        <a 
          href={`https://analytics.google.com/analytics/web/#/p${gaPropertyId.replace('G-', '')}/reports/intelligenthome`}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
          </svg>
          Open Full Analytics Dashboard
        </a>
        <a 
          href={`https://analytics.google.com/analytics/web/#/realtime/p${gaPropertyId.replace('G-', '')}`}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-50 transition"
        >
          <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
          View Realtime Data
        </a>
      </div>

      {/* Embedded Analytics Reports */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Traffic Overview */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          <div className="px-5 py-4 border-b border-gray-100 bg-gray-50">
            <h3 className="text-sm font-semibold text-gray-700">Traffic Overview (Last 7 Days)</h3>
          </div>
          <div className="p-6 text-center text-gray-500 text-sm">
            <p className="mb-3">To embed live charts, you'll need to set up the Google Analytics Reporting API.</p>
            <a 
              href="https://analytics.google.com" 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-blue-600 hover:text-blue-700 font-medium"
            >
              View in Google Analytics →
            </a>
          </div>
        </div>

        {/* Top Pages */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          <div className="px-5 py-4 border-b border-gray-100 bg-gray-50">
            <h3 className="text-sm font-semibold text-gray-700">Top Pages</h3>
          </div>
          <div className="p-6 text-center text-gray-500 text-sm">
            <p className="mb-3">See which pages your users visit most.</p>
            <a 
              href="https://analytics.google.com" 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-blue-600 hover:text-blue-700 font-medium"
            >
              View in Google Analytics →
            </a>
          </div>
        </div>
      </div>

      {/* Info Box */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex gap-3">
          <svg className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
          </svg>
          <div className="text-sm">
            <p className="font-medium text-blue-900 mb-1">Analytics Integration Active</p>
            <p className="text-blue-700">
              Your site is now tracking user behavior. Data appears in Google Analytics within 24-48 hours. 
              Use the links above to access detailed reports, realtime monitoring, and user insights.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

const fmtEUR = (cents) => `€${(cents / 100).toFixed(2)}`

export default function AdminDashboard() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [activeTab, setActiveTab] = useState('overview')

  useEffect(() => {
    axios.get('/api/admin/stats')
      .then(r => setStats(r.data))
      .catch(() => setError('Failed to load stats'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="p-8 text-gray-400 text-sm">Loading…</div>
  if (error)   return <div className="p-8 text-red-500 text-sm">{error}</div>

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-gray-900">Dashboard</h1>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex gap-6">
          <button
            onClick={() => setActiveTab('overview')}
            className={`pb-3 px-1 border-b-2 font-medium text-sm transition ${
              activeTab === 'overview'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Business Overview
          </button>
          <button
            onClick={() => setActiveTab('analytics')}
            className={`pb-3 px-1 border-b-2 font-medium text-sm transition ${
              activeTab === 'analytics'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Google Analytics
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
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
      )}

      {activeTab === 'analytics' && <GoogleAnalyticsDashboard />}
    </div>
  )
}
