import React, { useState } from 'react'
import axios from 'axios'
import { Send, Loader, AlertCircle, FileText } from 'lucide-react'

export default function Generate() {
  const [formData, setFormData] = useState({
    segment: 'new_phoenix',
    campaign_type: 'onboarding',
    recipient_count: 100,
  })
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const segments = [
    'cold_prospect',
    'new_phoenix',
    'active_phoenix',
    'upsell_candidate_visionary',
    'upsell_candidate_infinity',
    'churned',
    'reactivation',
  ]

  const campaignTypes = [
    'onboarding',
    'upsell_phoenix_visionary',
    'upsell_visionary_infinity',
    'reactivation',
    'cold_outbound',
  ]

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const response = await axios.post('/api/campaigns/generate', formData)
      setResult(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate campaign')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Generate Campaign</h1>
        <p className="text-gray-600 mt-2">Create a new email campaign with AI-powered generation</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Form */}
        <form onSubmit={handleSubmit} className="card space-y-6">
          <h2 className="text-xl font-semibold">Campaign Settings</h2>

          <div>
            <label className="block text-sm font-medium mb-2">Target Segment</label>
            <select
              name="segment"
              value={formData.segment}
              onChange={handleChange}
              className="input-field"
            >
              {segments.map(seg => (
                <option key={seg} value={seg}>
                  {seg.replace(/_/g, ' ').toUpperCase()}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Campaign Type</label>
            <select
              name="campaign_type"
              value={formData.campaign_type}
              onChange={handleChange}
              className="input-field"
            >
              {campaignTypes.map(type => (
                <option key={type} value={type}>
                  {type.replace(/_/g, ' ').toUpperCase()}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Recipient Count</label>
            <input
              type="number"
              name="recipient_count"
              value={formData.recipient_count}
              onChange={handleChange}
              className="input-field"
              min="1"
            />
          </div>

          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg flex gap-2 text-red-700 text-sm">
              <AlertCircle size={20} className="flex-shrink-0" />
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="btn-primary w-full flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <Loader size={20} className="animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <Send size={20} />
                Generate Campaign
              </>
            )}
          </button>
        </form>

        {/* Results */}
        {result && (
          <div className="space-y-6">
            <div className="card">
              <h2 className="text-xl font-semibold mb-4">Campaign Generated ✓</h2>
              <div className="space-y-3 text-sm">
                <div>
                  <strong>Campaign ID:</strong> {result.campaign_id}
                </div>
                <div>
                  <strong>Generated At:</strong> {new Date(result.generated_at).toLocaleString()}
                </div>
                <div>
                  <strong>Emails:</strong> {result.emails.length} sequences
                </div>
                <div>
                  <strong>Sources Used:</strong> {result.citations.length}
                </div>
              </div>

              {result.output_file && (
                <div className="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-200 text-sm">
                  <div className="flex items-center gap-2 text-blue-700">
                    <FileText size={16} />
                    <span>Saved to: <code className="font-mono">{result.output_file}</code></span>
                  </div>
                </div>
              )}
            </div>

            {/* Email Preview */}
            <div className="card">
              <h3 className="font-semibold mb-4">Email Preview</h3>
              <div className="space-y-4 max-h-96 overflow-y-auto">
                {result.emails.slice(0, 3).map((email, idx) => (
                  <div key={idx} className="border-l-4 border-ohm-gold pl-4 pb-4">
                    <h4 className="font-semibold text-sm">Email {email.step}: {email.subject}</h4>
                    <p className="text-xs text-gray-600 mt-2 line-clamp-2">{email.body}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Citations */}
            <div className="card">
              <h3 className="font-semibold mb-4">Sources Used</h3>
              <ul className="space-y-2 text-sm">
                {result.citations.map((cite, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="text-ohm-gold mt-1">•</span>
                    <div>
                      <a
                        href={cite.source_path}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="citation-link font-medium"
                      >
                        {cite.source_name}
                      </a>
                      <p className="text-gray-600 mt-1 line-clamp-2">{cite.excerpt}</p>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
