import React from 'react'
import { useTheme } from '../context/ThemeContext'

const Icon = {
  Sun: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"/>
    </svg>
  ),
  Moon: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"/>
    </svg>
  ),
  System: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
    </svg>
  ),
}

export default function ThemeSettings() {
  const { theme, setTheme } = useTheme()

  const themes = [
    { id: 'light', label: 'Light', icon: <Icon.Sun />, description: 'Always use light mode' },
    { id: 'dark', label: 'Dark', icon: <Icon.Moon />, description: 'Always use dark mode' },
  ]

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm">
      <div className="px-6 py-4 border-b border-gray-100 dark:border-gray-700">
        <p className="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">Appearance</p>
      </div>
      <div className="px-6 py-5 space-y-3">
        {themes.map(t => (
          <button
            key={t.id}
            onClick={() => setTheme(t.id)}
            className={`w-full flex items-center gap-4 p-4 rounded-lg border-2 transition-all ${
              theme === t.id
                ? 'border-gray-900 dark:border-gray-300 bg-gray-50 dark:bg-gray-700'
                : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
            }`}
          >
            <div className={`shrink-0 ${theme === t.id ? 'text-gray-900 dark:text-gray-100' : 'text-gray-400 dark:text-gray-500'}`}>
              {t.icon}
            </div>
            <div className="flex-1 text-left">
              <p className={`text-sm font-semibold ${theme === t.id ? 'text-gray-900 dark:text-gray-100' : 'text-gray-700 dark:text-gray-300'}`}>
                {t.label}
              </p>
              <p className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">{t.description}</p>
            </div>
            {theme === t.id && (
              <div className="shrink-0">
                <svg className="w-5 h-5 text-gray-900 dark:text-gray-100" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7"/>
                </svg>
              </div>
            )}
          </button>
        ))}
      </div>
    </div>
  )
}
