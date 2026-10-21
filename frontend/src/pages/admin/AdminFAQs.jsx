import React, { useEffect, useState } from 'react'
import axios from '../../utils/axios'

export default function AdminFAQs() {
  const [faqs, setFaqs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [editingId, setEditingId] = useState(null)
  const [showCreate, setShowCreate] = useState(false)
  const [formData, setFormData] = useState({ question: '', answer: '', position: 0, active: true })

  useEffect(() => {
    fetchFAQs()
  }, [])

  const fetchFAQs = async () => {
    try {
      setLoading(true)
      setError('')
      const res = await axios.get('/api/admin/faqs')
      setFaqs(res.data.faqs || [])
    } catch (err) {
      console.error('FAQ fetch error:', err)
      setError(err.response?.data?.error || err.message || 'Failed to load FAQs')
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async (e) => {
    e.preventDefault()
    try {
      await axios.post('/api/admin/faqs', formData)
      setFormData({ question: '', answer: '', position: 0, active: true })
      setShowCreate(false)
      fetchFAQs()
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to create FAQ')
    }
  }

  const handleUpdate = async (id) => {
    try {
      await axios.patch(`/api/admin/faqs/${id}`, formData)
      setEditingId(null)
      setFormData({ question: '', answer: '', position: 0, active: true })
      fetchFAQs()
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to update FAQ')
    }
  }

  const handleDelete = async (id) => {
    if (!confirm('Delete this FAQ?')) return
    try {
      await axios.delete(`/api/admin/faqs/${id}`)
      fetchFAQs()
    } catch (err) {
      setError('Failed to delete FAQ')
    }
  }

  const startEdit = (faq) => {
    setEditingId(faq.id)
    setFormData({
      question: faq.question,
      answer: faq.answer,
      position: faq.position,
      active: Boolean(faq.active)
    })
  }

  if (loading) return <div className="p-8 text-gray-400 dark:text-gray-500 text-sm">Loading…</div>
  if (error) return <div className="p-8 text-red-500 text-sm">{error}</div>

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-gray-900 dark:text-gray-100">FAQ Management</h1>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="px-4 py-2 bg-gray-900 dark:bg-gray-700 text-white text-sm font-semibold rounded-lg hover:bg-gray-700 dark:hover:bg-gray-600"
        >
          {showCreate ? 'Cancel' : '+ New FAQ'}
        </button>
      </div>

      {/* Create Form */}
      {showCreate && (
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 shadow-sm">
          <h2 className="text-base font-semibold mb-4 dark:text-gray-100">Create New FAQ</h2>
          <form onSubmit={handleCreate} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Question</label>
              <input
                type="text"
                value={formData.question}
                onChange={(e) => setFormData({ ...formData, question: e.target.value })}
                required
                className="w-full border border-gray-200 dark:border-gray-600 rounded-lg px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Answer</label>
              <textarea
                value={formData.answer}
                onChange={(e) => setFormData({ ...formData, answer: e.target.value })}
                required
                rows={4}
                className="w-full border border-gray-200 dark:border-gray-600 rounded-lg px-3 py-2 text-sm"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Position</label>
                <input
                  type="number"
                  value={formData.position}
                  onChange={(e) => setFormData({ ...formData, position: parseInt(e.target.value) })}
                  className="w-full border border-gray-200 dark:border-gray-600 rounded-lg px-3 py-2 text-sm"
                />
              </div>
              <div className="flex items-center gap-2 pt-7">
                <input
                  type="checkbox"
                  id="create-active"
                  checked={formData.active}
                  onChange={(e) => setFormData({ ...formData, active: e.target.checked })}
                  className="w-4 h-4"
                />
                <label htmlFor="create-active" className="text-sm text-gray-700 dark:text-gray-300">Active</label>
              </div>
            </div>
            <button
              type="submit"
              className="px-4 py-2 bg-gray-900 dark:bg-gray-700 text-white text-sm font-semibold rounded-lg hover:bg-gray-700 dark:hover:bg-gray-600"
            >
              Create FAQ
            </button>
          </form>
        </div>
      )}

      {/* FAQs List */}
      <div className="space-y-4">
        {faqs.length === 0 && (
          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-8 text-center">
            <p className="text-gray-400 dark:text-gray-500">No FAQs yet. Create one above.</p>
          </div>
        )}
        {faqs.map((faq) => (
          <div key={faq.id} className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 shadow-sm">
            {editingId === faq.id ? (
              <form onSubmit={(e) => { e.preventDefault(); handleUpdate(faq.id) }} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Question</label>
                  <input
                    type="text"
                    value={formData.question}
                    onChange={(e) => setFormData({ ...formData, question: e.target.value })}
                    required
                    className="w-full border border-gray-200 dark:border-gray-600 rounded-lg px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Answer</label>
                  <textarea
                    value={formData.answer}
                    onChange={(e) => setFormData({ ...formData, answer: e.target.value })}
                    required
                    rows={4}
                    className="w-full border border-gray-200 dark:border-gray-600 rounded-lg px-3 py-2 text-sm"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Position</label>
                    <input
                      type="number"
                      value={formData.position}
                      onChange={(e) => setFormData({ ...formData, position: parseInt(e.target.value) })}
                      className="w-full border border-gray-200 dark:border-gray-600 rounded-lg px-3 py-2 text-sm"
                    />
                  </div>
                  <div className="flex items-center gap-2 pt-7">
                    <input
                      type="checkbox"
                      id={`edit-active-${faq.id}`}
                      checked={formData.active}
                      onChange={(e) => setFormData({ ...formData, active: e.target.checked })}
                      className="w-4 h-4"
                    />
                    <label htmlFor={`edit-active-${faq.id}`} className="text-sm text-gray-700 dark:text-gray-300">Active</label>
                  </div>
                </div>
                <div className="flex gap-2">
                  <button
                    type="submit"
                    className="px-4 py-2 bg-gray-900 dark:bg-gray-700 text-white text-sm font-semibold rounded-lg hover:bg-gray-700 dark:hover:bg-gray-600"
                  >
                    Save
                  </button>
                  <button
                    type="button"
                    onClick={() => { setEditingId(null); setFormData({ question: '', answer: '', position: 0, active: true }) }}
                    className="px-4 py-2 border border-gray-200 dark:border-gray-600 text-gray-700 dark:text-gray-300 text-sm font-medium rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            ) : (
              <div>
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-xs bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 px-2 py-0.5 rounded font-mono">
                        #{faq.id} · Pos: {faq.position}
                      </span>
                      {faq.active ? (
                        <span className="text-xs bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 px-2 py-0.5 rounded">Active</span>
                      ) : (
                        <span className="text-xs bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 px-2 py-0.5 rounded">Inactive</span>
                      )}
                    </div>
                    <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100 mb-2">{faq.question}</h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400 whitespace-pre-wrap">{faq.answer}</p>
                  </div>
                  <div className="flex gap-2 ml-4">
                    <button
                      onClick={() => startEdit(faq)}
                      className="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDelete(faq.id)}
                      className="text-sm text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
