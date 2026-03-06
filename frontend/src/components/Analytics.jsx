import React, { useEffect, useState } from 'react'
import axios from 'axios'
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { TrendingUp, TrendingDown } from 'lucide-react'

export default function Analytics() {
  const [weeklyReport, setWeeklyReport] = useState(null)
  const [metrics, setMetrics] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [reportRes, metricsRes] = await Promise.all([
          axios.get('/api/analytics/weekly-report'),
          axios.get('/api/analytics/metrics'),
        ])
        setWeeklyReport(reportRes.data)
        setMetrics(metricsRes.data)
      } catch (err) {
        setError('Failed to load analytics')
        console.error(err)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  if (loading) return <div className="text-center p-8">Loading analytics...</div>
  if (error) return <div className="text-red-600 p-4">{error}</div>

  // Mock data for charts
  const chartData = [
    { day: 'Mon', opens: 240, clicks: 80, conversions: 24 },
    { day: 'Tue', opens: 320, clicks: 110, conversions: 35 },
    { day: 'Wed', opens: 280, clicks: 95, conversions: 28 },
    { day: 'Thu', opens: 380, clicks: 130, conversions: 42 },
    { day: 'Fri', opens: 350, clicks: 120, conversions: 38 },
    { day: 'Sat', opens: 220, clicks: 70, conversions: 18 },
    { day: 'Sun', opens: 180, clicks: 60, conversions: 15 },
  ]

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Analytics</h1>
        <p className="text-gray-600 mt-2">Email performance metrics and engagement tracking</p>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Total Opens"
          value={metrics?.total_opens}
          change="+12%"
          trend="up"
        />
        <MetricCard
          title="Open Rate"
          value={`${(metrics?.avg_open_rate * 100).toFixed(1)}%`}
          change="+2.3%"
          trend="up"
        />
        <MetricCard
          title="Click Rate"
          value={`${(metrics?.avg_ctr * 100).toFixed(1)}%`}
          change="-0.5%"
          trend="down"
        />
        <MetricCard
          title="Conversions"
          value={metrics?.total_conversions}
          change="+8%"
          trend="up"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Open/Click Trend */}
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Weekly Engagement Trend</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="day" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="opens"
                stroke="#D4AF37"
                name="Opens"
                strokeWidth={2}
              />
              <Line
                type="monotone"
                dataKey="clicks"
                stroke="#3b82f6"
                name="Clicks"
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Conversion Funnel */}
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Conversion Funnel</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="day" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="opens" fill="#D4AF37" name="Opens" />
              <Bar dataKey="clicks" fill="#3b82f6" name="Clicks" />
              <Bar dataKey="conversions" fill="#10b981" name="Conversions" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Weekly Report */}
      {weeklyReport && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Top Performers */}
          <div className="card">
            <h3 className="text-lg font-semibold mb-4">Top Performers</h3>
            <div className="space-y-4">
              <ReportItem label="Best Campaign" value={weeklyReport.top_campaign} />
              <ReportItem label="Best Send Time" value={weeklyReport.best_time || 'Tuesday 10:00 AM'} />
              <ReportItem label="Subject Pattern" value="Alignment and Renewal" />
              <ReportItem label="Best Segment" value={weeklyReport.best_segment || 'Active Phoenix'} />
            </div>
          </div>

          {/* Suggestions */}
          <div className="card">
            <h3 className="text-lg font-semibold mb-4">Optimization Suggestions</h3>
            {weeklyReport.subject_suggestions && weeklyReport.subject_suggestions.length > 0 ? (
              <ul className="space-y-2">
                {weeklyReport.subject_suggestions.slice(0, 4).map((suggestion, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-sm">
                    <span className="text-ohm-gold font-bold">→</span>
                    <span className="text-gray-700">{suggestion}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-gray-600 text-sm">Run weekly optimization to get suggestions</p>
            )}
          </div>
        </div>
      )}

      {/* Underperformers */}
      {weeklyReport?.underperformers && weeklyReport.underperformers.length > 0 && (
        <div className="card bg-yellow-50 border border-yellow-200">
          <h3 className="text-lg font-semibold mb-4 text-yellow-900">⚠️ Campaigns to Review</h3>
          <p className="text-sm text-yellow-800 mb-3">
            These campaigns have below-average open rates. Consider adjusting subject lines or send times.
          </p>
          <div className="space-y-2">
            {weeklyReport.underperformers.map((campaign, idx) => (
              <div key={idx} className="text-sm text-yellow-900">
                • {campaign}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function MetricCard({ title, value, change, trend }) {
  return (
    <div className="card">
      <p className="text-gray-600 text-sm mb-1">{title}</p>
      <div className="flex items-end justify-between">
        <p className="text-3xl font-bold text-gray-900">{value}</p>
        <div className={`flex items-center gap-1 text-sm ${trend === 'up' ? 'text-green-600' : 'text-red-600'}`}>
          {trend === 'up' ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
          {change}
        </div>
      </div>
    </div>
  )
}

function ReportItem({ label, value }) {
  return (
    <div className="flex justify-between items-start">
      <span className="text-gray-600 text-sm">{label}</span>
      <span className="font-semibold text-gray-900 text-right">{value}</span>
    </div>
  )
}
