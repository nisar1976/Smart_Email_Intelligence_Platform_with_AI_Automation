import React, { useEffect, useState } from 'react'
import axios from 'axios'
import { Users, RefreshCw } from 'lucide-react'

export default function Segments() {
  const [segments, setSegments] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchSegments = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await axios.get('/api/segments/')
      setSegments(response.data)
    } catch (err) {
      setError('Failed to load segments')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchSegments()
  }, [])

  if (loading) {
    return <div className="text-center p-8">Loading segments...</div>
  }

  if (error) {
    return <div className="text-red-600 p-4">{error}</div>
  }

  const totalContacts = segments
    ? Object.values(segments).reduce((sum, seg) => sum + (seg.contact_count || 0), 0)
    : 0

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Audience Segments</h1>
          <p className="text-gray-600 mt-2">Behavioral audience segmentation for targeted campaigns</p>
        </div>
        <button
          onClick={fetchSegments}
          className="btn-secondary flex items-center gap-2"
        >
          <RefreshCw size={16} />
          Refresh
        </button>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <SummaryCard title="Total Contacts" value={totalContacts} />
        <SummaryCard title="Total Segments" value={segments ? Object.keys(segments).length : 0} />
        <SummaryCard title="Largest Segment" value="Active Phoenix" />
        <SummaryCard title="Churn Risk" value="42 contacts" />
      </div>

      {/* Segments Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {segments && Object.entries(segments).map(([key, segment]) => (
          <div key={key} className="card hover:shadow-md transition-shadow">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="p-3 bg-blue-100 rounded-lg">
                  <Users className="text-blue-600" size={24} />
                </div>
                <div>
                  <h3 className="font-semibold text-lg capitalize">
                    {segment.name.replace(/_/g, ' ')}
                  </h3>
                  <p className="text-gray-600 text-sm">
                    {segment.contact_count} contacts
                  </p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold text-ohm-gold">
                  {((segment.contact_count / totalContacts) * 100).toFixed(0)}%
                </p>
              </div>
            </div>

            {/* Progress Bar */}
            <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
              <div
                className="bg-ohm-gold h-2 rounded-full transition-all"
                style={{
                  width: `${(segment.contact_count / totalContacts) * 100}%`
                }}
              />
            </div>

            {/* Sample Contacts */}
            {segment.contacts && segment.contacts.length > 0 && (
              <div className="mt-4">
                <p className="text-xs font-semibold text-gray-600 mb-2">Sample Contacts</p>
                <div className="space-y-1">
                  {segment.contacts.slice(0, 3).map((contact, idx) => (
                    <div key={idx} className="text-xs text-gray-500">
                      {contact}
                    </div>
                  ))}
                  {segment.contacts.length > 3 && (
                    <div className="text-xs text-gray-400 italic">
                      +{segment.contacts.length - 3} more
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Segment Descriptions */}
      <div className="card">
        <h2 className="text-xl font-semibold mb-4">Segment Definitions</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
          <SegmentDef
            name="Cold Prospect"
            desc="No purchase history, minimal engagement in 30+ days"
          />
          <SegmentDef
            name="New Phoenix"
            desc="Recently subscribed to Phoenix tier (< 7 days)"
          />
          <SegmentDef
            name="Active Phoenix"
            desc="Phoenix member, engaged in last 14 days, not upsold"
          />
          <SegmentDef
            name="Upsell Candidate - Visionary"
            desc="Active Phoenix for 30+ days, clicked upsell CTA"
          />
          <SegmentDef
            name="Upsell Candidate - Infinity"
            desc="Active Visionary for 30+ days, clicked upsell CTA"
          />
          <SegmentDef
            name="Churned"
            desc="Cancelled subscription or no login in 60+ days"
          />
          <SegmentDef
            name="Reactivation"
            desc="Churned > 90 days, previously very active"
          />
        </div>
      </div>
    </div>
  )
}

function SummaryCard({ title, value }) {
  return (
    <div className="card text-center">
      <p className="text-gray-600 text-sm mb-2">{title}</p>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
    </div>
  )
}

function SegmentDef({ name, desc }) {
  return (
    <div className="p-3 border border-gray-200 rounded-lg">
      <h4 className="font-semibold text-gray-900">{name}</h4>
      <p className="text-gray-600 text-xs mt-1">{desc}</p>
    </div>
  )
}
