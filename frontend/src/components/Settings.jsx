import React, { useEffect, useState } from 'react'
import axios from 'axios'
import { Save, Eye, EyeOff, AlertCircle, CheckCircle, Loader } from 'lucide-react'

export default function Settings() {
  const [settings, setSettings] = useState({
    openai_api_key: '',
    gmail_email: '',
    gmail_app_password: '',
    crm_provider: 'hubspot',
    crm_api_key: '',
    stripe_secret_key: '',
    stripe_webhook_secret: '',
  })
  const [showPasswords, setShowPasswords] = useState({
    openai: false,
    gmail: false,
    crm: false,
    stripe: false,
  })
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState(null)
  const [testResults, setTestResults] = useState(null)
  const [testing, setTesting] = useState(false)

  useEffect(() => {
    fetchSettings()
  }, [])

  const fetchSettings = async () => {
    try {
      const response = await axios.get('/api/settings/')
      setSettings(response.data)
    } catch (error) {
      console.error('Failed to load settings:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleChange = (e) => {
    const { name, value } = e.target
    setSettings(prev => ({ ...prev, [name]: value }))
  }

  const handleSave = async () => {
    setSaving(true)
    setMessage(null)

    try {
      await axios.post('/api/settings/', settings)
      setMessage({ type: 'success', text: 'Settings saved successfully!' })
      setTimeout(() => setMessage(null), 3000)
    } catch (error) {
      setMessage({
        type: 'error',
        text: error.response?.data?.detail || 'Failed to save settings'
      })
    } finally {
      setSaving(false)
    }
  }

  const handleTest = async () => {
    setTesting(true)
    try {
      const response = await axios.post('/api/settings/test')
      setTestResults(response.data.results)
    } catch (error) {
      setMessage({
        type: 'error',
        text: 'Failed to test settings'
      })
    } finally {
      setTesting(false)
    }
  }

  if (loading) {
    return <div className="text-center p-8">Loading settings...</div>
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600 mt-2">Configure API keys and credentials</p>
      </div>

      {message && (
        <div className={`p-4 rounded-lg border flex gap-3 ${
          message.type === 'success'
            ? 'bg-green-50 border-green-200 text-green-700'
            : 'bg-red-50 border-red-200 text-red-700'
        }`}>
          {message.type === 'success' ? <CheckCircle size={20} /> : <AlertCircle size={20} />}
          <span>{message.text}</span>
        </div>
      )}

      <div className="max-w-2xl space-y-6">
        {/* OpenAI Configuration */}
        <div className="card">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            OpenAI API
          </h2>
          <div className="space-y-4">
            <PasswordField
              label="API Key"
              name="openai_api_key"
              value={settings.openai_api_key}
              onChange={handleChange}
              show={showPasswords.openai}
              onToggle={() => setShowPasswords(prev => ({
                ...prev,
                openai: !prev.openai
              }))}
              placeholder="sk-proj-..."
              help="Get your key from https://platform.openai.com/api-keys"
            />
          </div>
        </div>

        {/* Gmail Configuration */}
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Gmail SMTP</h2>
          <div className="space-y-4">
            <InputField
              label="Gmail Email Address"
              name="gmail_email"
              value={settings.gmail_email}
              onChange={handleChange}
              placeholder="your-email@gmail.com"
              help="The Gmail account that will send emails"
            />
            <PasswordField
              label="App Password"
              name="gmail_app_password"
              value={settings.gmail_app_password}
              onChange={handleChange}
              show={showPasswords.gmail}
              onToggle={() => setShowPasswords(prev => ({
                ...prev,
                gmail: !prev.gmail
              }))}
              placeholder="xxxx-xxxx-xxxx-xxxx"
              help={
                <>
                  Get your 16-character app password from{' '}
                  <a
                    href="https://myaccount.google.com/apppasswords"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="citation-link"
                  >
                    Google Account
                  </a>
                </>
              }
            />
          </div>
        </div>

        {/* CRM Configuration */}
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">CRM Integration</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">CRM Provider</label>
              <select
                name="crm_provider"
                value={settings.crm_provider}
                onChange={handleChange}
                className="input-field"
              >
                <option value="hubspot">HubSpot</option>
                <option value="convertkit">ConvertKit</option>
              </select>
            </div>
            <PasswordField
              label="API Key"
              name="crm_api_key"
              value={settings.crm_api_key}
              onChange={handleChange}
              show={showPasswords.crm}
              onToggle={() => setShowPasswords(prev => ({
                ...prev,
                crm: !prev.crm
              }))}
              placeholder="Your CRM API key"
              help="HubSpot: Get from Settings → Integrations → API. ConvertKit: Get from Creator Network → API."
            />
          </div>
        </div>

        {/* Stripe Configuration */}
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Stripe</h2>
          <div className="space-y-4">
            <PasswordField
              label="Secret Key"
              name="stripe_secret_key"
              value={settings.stripe_secret_key}
              onChange={handleChange}
              show={showPasswords.stripe}
              onToggle={() => setShowPasswords(prev => ({ ...prev, stripe: !prev.stripe }))}
              placeholder="sk_live_... or sk_test_..."
              help="Get from Stripe Dashboard → Developers → API keys"
            />
            <PasswordField
              label="Webhook Secret"
              name="stripe_webhook_secret"
              value={settings.stripe_webhook_secret}
              onChange={handleChange}
              show={showPasswords.stripe}
              onToggle={() => setShowPasswords(prev => ({ ...prev, stripe: !prev.stripe }))}
              placeholder="whsec_..."
              help="Get from Stripe Dashboard → Developers → Webhooks → your endpoint → Signing secret"
            />
          </div>
        </div>

        {/* Test Credentials */}
        <button
          onClick={handleTest}
          disabled={testing}
          className="btn-secondary w-full flex items-center justify-center gap-2"
        >
          {testing ? (
            <>
              <Loader size={16} className="animate-spin" />
              Testing...
            </>
          ) : (
            <>
              Test Connections
            </>
          )}
        </button>

        {testResults && (
          <div className="card bg-gray-50 border-2 border-gray-200">
            <h3 className="font-semibold mb-3">Connection Status</h3>
            <div className="space-y-2 text-sm">
              {Object.entries(testResults).map(([service, status]) => (
                <div key={service} className="flex items-center justify-between">
                  <span className="capitalize font-medium">{service}</span>
                  <span className={`font-mono ${
                    status.includes('✓') ? 'text-green-600' : status.includes('⚠') ? 'text-yellow-600' : 'text-red-600'
                  }`}>
                    {status}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Save Button */}
        <button
          onClick={handleSave}
          disabled={saving}
          className="btn-primary w-full flex items-center justify-center gap-2"
        >
          {saving ? (
            <>
              <Loader size={20} className="animate-spin" />
              Saving...
            </>
          ) : (
            <>
              <Save size={20} />
              Save Settings
            </>
          )}
        </button>
      </div>

      {/* Security Notice */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm text-blue-900">
        <p className="font-semibold mb-2">🔒 Security Notice</p>
        <ul className="list-disc list-inside space-y-1">
          <li>API keys are stored securely in settings_store.json</li>
          <li>Passwords are never sent to frontend in plaintext</li>
          <li>Never share your API keys publicly</li>
          <li>Rotate keys periodically for security</li>
        </ul>
      </div>
    </div>
  )
}

function InputField({ label, name, value, onChange, placeholder, help }) {
  return (
    <div>
      <label className="block text-sm font-medium mb-2">{label}</label>
      <input
        type="text"
        name={name}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        className="input-field"
      />
      {help && <p className="text-xs text-gray-600 mt-1">{help}</p>}
    </div>
  )
}

function PasswordField({
  label,
  name,
  value,
  onChange,
  show,
  onToggle,
  placeholder,
  help
}) {
  return (
    <div>
      <label className="block text-sm font-medium mb-2">{label}</label>
      <div className="relative">
        <input
          type={show ? 'text' : 'password'}
          name={name}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          className="input-field pr-10"
        />
        <button
          type="button"
          onClick={onToggle}
          className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
        >
          {show ? <EyeOff size={18} /> : <Eye size={18} />}
        </button>
      </div>
      {help && <p className="text-xs text-gray-600 mt-1">{help}</p>}
    </div>
  )
}
