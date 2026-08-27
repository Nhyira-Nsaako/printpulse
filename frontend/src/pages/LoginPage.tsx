import React, { useState } from 'react'

interface Props {
  onLogin: (username: string, password: string) => Promise<boolean>
  error: string | null
}

export function LoginPage({ onLogin, error }: Props) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    await onLogin(username, password)
    setLoading(false)
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-logo">
          <span className="logo-pulse" />
          <span className="logo-text">PrintPulse</span>
        </div>
        <p className="login-sub">Faultline Command Center</p>
        <form onSubmit={handleSubmit} className="login-form">
          <label className="field-label">Username</label>
          <input
            className="input"
            type="text"
            autoComplete="username"
            value={username}
            onChange={e => setUsername(e.target.value)}
            required
          />
          <label className="field-label">Password</label>
          <input
            className="input"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            required
          />
          {error && <div className="login-error">{error}</div>}
          <button className="btn btn--primary btn--full" type="submit" disabled={loading}>
            {loading ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
      </div>
    </div>
  )
}
