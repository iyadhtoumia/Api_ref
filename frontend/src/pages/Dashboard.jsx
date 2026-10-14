import React, { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import axios from '../utils/axios'

export default function Dashboard() {
  const { user, signout, refreshUser } = useAuth()
  const [serial, setSerial] = useState('')
  const [loading, setLoading] = useState(false)
  const [deviceInfo, setDeviceInfo] = useState(null)
  const [configResult, setConfigResult] = useState(null)
  const [error, setError] = useState('')
  const [activeTab, setActiveTab] = useState('config') // 'lookup' or 'config'

  const handleDeviceLookup = async (e) => {
    e.preventDefault()
    
    if (serial.length < 4) {
      setError('Serial number too short. Please enter a valid serial.')
      return
    }

    setLoading(true)
    setError('')
    setDeviceInfo(null)

    try {
      const response = await axios.post('/api/lookup', { serial })
      setDeviceInfo(response.data)
    } catch (err) {
      const errorMsg = err.response?.data?.error || 'Failed to lookup device'
      setError(errorMsg)
    } finally {
      setLoading(false)
    }
  }

  const handleConfigLookup = async (e) => {
    e.preventDefault()
    
    if (user.coins < 10) {
      setError('Insufficient coins. You need at least 10 coins.')
      return
    }

    if (serial.length < 4) {
      setError('Serial number too short. Please enter a valid serial.')
      return
    }

    setLoading(true)
    setError('')
    setConfigResult(null)

    try {
      // NO TIMEOUT - let it run as long as needed (same as Telegram bot)
      const response = await axios.post('/api/lookup-config', { serial })
      setConfigResult(response.data)
      await refreshUser()
    } catch (err) {
      const errorMsg = err.response?.data?.error || 'Failed to lookup configuration'
      const debugInfo = err.response?.data?.debug
      setError(debugInfo ? `${errorMsg}\n\n${debugInfo}` : errorMsg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-background min-h-screen text-on-surface antialiased">
      <nav className="bg-surface-container border-b border-surface-container-highest">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-primary-container to-secondary flex items-center justify-center">
                <svg className="w-4 h-4 text-on-primary" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" viewBox="0 0 24 24">
                  <path d="M12 2L2 7l10 5 10-5-10-5z"></path>
                  <path d="M2 17l10 5 10-5"></path>
                  <path d="M2 12l10 5 10-5"></path>
                </svg>
              </div>
              <span className="text-lg font-semibold">Apple Config Lookup</span>
            </div>
            
            <div className="flex items-center gap-4">
              <div className="bg-surface-container-high px-4 py-2 rounded-lg flex items-center gap-2">
                <span className="material-symbols-outlined text-tertiary text-lg">
                  monetization_on
                </span>
                <span className="font-semibold">{user?.coins || 0}</span>
                <span className="text-sm text-on-surface-variant">coins</span>
              </div>
              
              <button
                onClick={signout}
                className="text-sm text-on-surface-variant hover:text-on-surface px-3 py-2 rounded-lg hover:bg-surface-container-high"
              >
                Sign Out
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-4xl mx-auto px-4 py-12">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold mb-2">Apple Device Lookup</h1>
          <p className="text-on-surface-variant">Lookup device info or get logic board configuration</p>
        </div>

        {/* Tabs - same as Telegram bot commands */}
        <div className="flex gap-2 mb-6 justify-center">
          <button
            onClick={() => setActiveTab('lookup')}
            className={`px-6 py-2 rounded-lg font-medium transition-colors ${
              activeTab === 'lookup'
                ? 'bg-primary text-on-primary'
                : 'bg-surface-container text-on-surface-variant hover:bg-surface-container-high'
            }`}
          >
             Device Info
          </button>
          <button
            onClick={() => setActiveTab('config')}
            className={`px-6 py-2 rounded-lg font-medium transition-colors ${
              activeTab === 'config'
                ? 'bg-primary text-on-primary'
                : 'bg-surface-container text-on-surface-variant hover:bg-surface-container-high'
            }`}
          >
             Configuration (10 coins)
          </button>
        </div>

        <div className="bg-surface-container/90 backdrop-blur-xl rounded-2xl p-8 shadow-xl">
          {/* Device Lookup Form (same as /lookup command) */}
          {activeTab === 'lookup' && (
            <form onSubmit={handleDeviceLookup} className="space-y-6">
              <div>
                <label htmlFor="serial" className="block text-sm font-medium text-on-surface-variant mb-2">
                  Serial Number
                </label>
                <input
                  type="text"
                  id="serial"
                  value={serial}
                  onChange={(e) => setSerial(e.target.value.toUpperCase())}
                  placeholder="C02P73J9G8WP"
                  className="w-full bg-surface-container-lowest text-on-surface placeholder:text-outline-variant px-4 py-3 rounded-lg focus:bg-surface-container-low focus:outline-none text-center text-lg tracking-wider font-mono"
                  required
                  minLength={4}
                  maxLength={20}
                />
                <p className="text-xs text-outline mt-2">
                  Get device model and type (FREE)
                </p>
              </div>

              {error && (
                <div className="p-4 bg-error/10 border border-error/20 rounded-lg">
                  <p className="text-sm text-error whitespace-pre-line">{error}</p>
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 px-4 rounded-lg bg-tertiary hover:bg-tertiary-fixed text-on-tertiary font-semibold disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <span className="w-5 h-5 border-2 border-on-tertiary border-t-transparent rounded-full animate-spin"></span>
                    Looking up...
                  </>
                ) : (
                  <>
                    <span className="material-symbols-outlined">search</span>
                    Lookup Device Info 
                  </>
                )}
              </button>

              {deviceInfo && deviceInfo.success && (
                <div className="mt-6 p-6 bg-surface-container-high rounded-xl border border-tertiary/20">
                  <div className="flex items-center gap-2 mb-4">
                    <span className="material-symbols-outlined text-tertiary">check_circle</span>
                    <h3 className="text-lg font-semibold">Device Found</h3>
                  </div>
                  
                  <div className="space-y-3">
                    <div>
                      <p className="text-sm text-on-surface-variant mb-1">Model</p>
                      <p className="font-semibold text-tertiary text-lg">{deviceInfo.model}</p>
                    </div>
                    
                    <div>
                      <p className="text-sm text-on-surface-variant mb-1">Device Type</p>
                      <p className="font-mono text-on-surface">{deviceInfo.device_type}</p>
                    </div>
                  </div>
                </div>
              )}
            </form>
          )}

          {/* Config Lookup Form (same as /config command) */}
          {activeTab === 'config' && (
            <form onSubmit={handleConfigLookup} className="space-y-6">
              <div>
                <label htmlFor="serial-config" className="block text-sm font-medium text-on-surface-variant mb-2">
                  Serial Number
                </label>
                <input
                  type="text"
                  id="serial-config"
                  value={serial}
                  onChange={(e) => setSerial(e.target.value.toUpperCase())}
                  placeholder="C02P73J9G8WP"
                  className="w-full bg-surface-container-lowest text-on-surface placeholder:text-outline-variant px-4 py-3 rounded-lg focus:bg-surface-container-low focus:outline-none text-center text-lg tracking-wider font-mono"
                  required
                  minLength={4}
                  maxLength={20}
                />
                <p className="text-xs text-outline mt-2">
                  Cost: 10 coins | Cached results: Free
                </p>
              </div>

              {error && (
                <div className="p-4 bg-error/10 border border-error/20 rounded-lg">
                  <p className="text-sm text-error whitespace-pre-line">{error}</p>
                </div>
              )}

              <button
                type="submit"
                disabled={loading || user.coins < 10}
                className="w-full py-3 px-4 rounded-lg bg-primary hover:bg-primary-fixed text-on-primary font-semibold disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {loading ? (
                  <div className="flex flex-col items-center gap-2 py-2">
                    <div className="flex items-center gap-2">
                      <span className="w-5 h-5 border-2 border-on-primary border-t-transparent rounded-full animate-spin"></span>
                      <span>Scraping Apple website...</span>
                    </div>
                    <span className="text-xs opacity-75">Please wait, this can take up to 1 minute</span>
                    <span className="text-xs opacity-60">Do not close this page</span>
                  </div>
                ) : (
                  <>
                    <span className="material-symbols-outlined">build</span>
                    Get Configuration (10 coins)
                  </>
                )}
              </button>

              {configResult && configResult.success && (
                <div className="mt-6 p-6 bg-surface-container-high rounded-xl border border-tertiary/20">
                  <div className="flex items-center gap-2 mb-4">
                    <span className="material-symbols-outlined text-tertiary">check_circle</span>
                    <h3 className="text-lg font-semibold">Configuration Retrieved</h3>
                  </div>
                  
                  <div className="space-y-3">
                    <div>
                      <p className="text-sm text-on-surface-variant mb-1">Serial Number</p>
                      <p className="font-mono text-on-surface">{configResult.serial}</p>
                    </div>
                    
                    <div>
                      <p className="text-sm text-on-surface-variant mb-1">Logic Board Configuration</p>
                      <p className="font-semibold text-tertiary text-lg">{configResult.config}</p>
                    </div>

                    {configResult.cached && (
                      <div className="mt-4 p-3 bg-tertiary-container/10 rounded-lg">
                        <p className="text-xs text-tertiary flex items-center gap-1">
                          <span className="material-symbols-outlined text-sm">bolt</span>
                          Retrieved instantly from cache (no coins deducted)
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </form>
          )}
        </div>

        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-surface-container p-6 rounded-xl">
            <div className="text-2xl font-bold text-primary mb-1">{user?.coins || 0}</div>
            <div className="text-sm text-on-surface-variant">Available Coins</div>
          </div>
          
          <div className="bg-surface-container p-6 rounded-xl">
            <div className="text-2xl font-bold text-tertiary mb-1">{user?.total_lookups || 0}</div>
            <div className="text-sm text-on-surface-variant">Total Lookups</div>
          </div>
          
          <div className="bg-surface-container p-6 rounded-xl">
            <div className="text-2xl font-bold text-secondary mb-1">10</div>
            <div className="text-sm text-on-surface-variant">Coins per Config</div>
          </div>
        </div>

     
      </main>
    </div>
  )
}
