import React, { useEffect, useState } from 'react'
import axios from 'axios'
import { Mail, Users, TrendingUp, BarChart3 } from 'lucide-react'
import { Link } from 'react-router-dom'

export default function Dashboard() {
  const [metrics, setMetrics] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const response = await axios.get('/api/analytics/metrics?days=7')
        setMetrics(response.data)
      } catch (err) {
        setError('Failed to load metrics')
        console.error(err)
      } finally {
        setLoading(false)
      }
    }

    fetchMetrics()
  }, [])

  if (error) {
    return <div className="text-red-600 p-4">{error}</div>
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600 mt-2">Welcome to OHM Email Intelligence Agent</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Emails Sent"
          value={metrics?.total_emails_sent || '—'}
          icon={<Mail className="text-blue-500" />}
        />
        <StatCard
          title="Open Rate"
          value={metrics?.avg_open_rate ? `${(metrics.avg_open_rate * 100).toFixed(1)}%` : '—'}
          icon={<TrendingUp className="text-green-500" />}
        />
        <StatCard
          title="Click-Through Rate"
          value={metrics?.avg_ctr ? `${(metrics.avg_ctr * 100).toFixed(1)}%` : '—'}
          icon={<BarChart3 className="text-purple-500" />}
        />
        <StatCard
          title="Conversions"
          value={metrics?.total_conversions || '—'}
          icon={<TrendingUp className="text-orange-500" />}
        />
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
        <h2 className="text-xl font-semibold mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link
            to="/generate"
            className="p-4 border-2 border-ohm-gold text-center rounded-lg hover:bg-ohm-gold hover:text-black transition-colors"
          >
            <Mail className="mx-auto mb-2" />
            <div className="font-semibold">Generate Campaign</div>
            <div className="text-sm text-gray-600">Create new email sequence</div>
          </Link>

          <Link
            to="/segments"
            className="p-4 border-2 border-gray-300 text-center rounded-lg hover:border-ohm-gold transition-colors"
          >
            <Users className="mx-auto mb-2" />
            <div className="font-semibold">View Segments</div>
            <div className="text-sm text-gray-600">Check audience breakdown</div>
          </Link>

          <Link
            to="/analytics"
            className="p-4 border-2 border-gray-300 text-center rounded-lg hover:border-ohm-gold transition-colors"
          >
            <BarChart3 className="mx-auto mb-2" />
            <div className="font-semibold">View Analytics</div>
            <div className="text-sm text-gray-600">Review performance metrics</div>
          </Link>
        </div>
      </div>

      {/* Top Performers */}
      {metrics && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="card">
            <h3 className="text-lg font-semibold mb-4">Top Insights</h3>
            <ul className="space-y-2 text-sm">
              <li>🏆 Best Segment: <strong>{metrics.top_segment}</strong></li>
              <li>🕐 Best Send Time: <strong>{metrics.best_time}</strong></li>
              <li>📝 Best Subject: <strong>{metrics.best_subject_pattern}</strong></li>
              <li>📊 Conversion Rate: <strong>{(metrics.avg_conversion_rate * 100).toFixed(2)}%</strong></li>
            </ul>
          </div>

          <div className="card">
            <h3 className="text-lg font-semibold mb-4">This Week</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Total Opens:</span>
                <strong>{metrics.total_opens}</strong>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Total Clicks:</span>
                <strong>{metrics.total_clicks}</strong>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">New Conversions:</span>
                <strong>{metrics.total_conversions}</strong>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function StatCard({ title, value, icon }) {
  return (
    <div className="card flex items-start gap-4">
      <div className="p-3 bg-gray-100 rounded-lg">{icon}</div>
      <div className="flex-1">
        <p className="text-gray-600 text-sm">{title}</p>
        <p className="text-2xl font-bold text-gray-900">{value}</p>
      </div>
    </div>
  )
}
