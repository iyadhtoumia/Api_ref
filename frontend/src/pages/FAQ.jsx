import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import axios from '../utils/axios'

export default function FAQ() {
  const [faqs, setFaqs] = useState([])
  const [loading, setLoading] = useState(true)
  const [openId, setOpenId] = useState(null)

  useEffect(() => {
    axios.get('/api/faqs')
      .then(res => setFaqs(res.data.faqs || []))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const toggleFAQ = (id) => {
    setOpenId(openId === id ? null : id)
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link to="/dashboard" className="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 text-sm flex items-center gap-2">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Back to Dashboard
          </Link>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-4xl mx-auto px-6 py-12">
        <div className="text-center mb-12">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-3">Frequently Asked Questions</h1>
          <p className="text-gray-600 dark:text-gray-400">Find answers to common questions about our service</p>
        </div>

        {loading ? (
          <div className="text-center py-12 text-gray-400 dark:text-gray-500">Loading FAQs…</div>
        ) : faqs.length === 0 ? (
          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-12 text-center">
            <p className="text-gray-400 dark:text-gray-500">No FAQs available at the moment.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {faqs.map((faq) => (
              <div
                key={faq.id}
                className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden shadow-sm"
              >
                <button
                  onClick={() => toggleFAQ(faq.id)}
                  className="w-full flex items-center justify-between px-6 py-4 text-left hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                >
                  <span className="font-semibold text-gray-900 dark:text-gray-100 pr-4">{faq.question}</span>
                  <svg
                    className={`w-5 h-5 text-gray-400 dark:text-gray-500 flex-shrink-0 transition-transform ${
                      openId === faq.id ? 'rotate-180' : ''
                    }`}
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                {openId === faq.id && (
                  <div className="px-6 pb-4 border-t border-gray-100 dark:border-gray-700 pt-4">
                    <p className="text-gray-600 dark:text-gray-400 whitespace-pre-wrap leading-relaxed">
                      {faq.answer}
                    </p>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Contact Section */}
        <div className="mt-12 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-6 text-center">
          <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">Still have questions?</h3>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
            Can't find the answer you're looking for? Contact our support team.
          </p>
          <Link
            to="/dashboard"
            className="inline-block px-5 py-2 bg-gray-900 dark:bg-gray-700 text-white text-sm font-semibold rounded-lg hover:bg-gray-700 dark:hover:bg-gray-600 transition-colors"
          >
            Contact Support
          </Link>
        </div>
      </main>
    </div>
  )
}
