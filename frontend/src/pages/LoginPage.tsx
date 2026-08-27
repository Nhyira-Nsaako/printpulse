import React, { useState } from 'react'

interface Props {
  onLogin: (username: string, password: string) => Promise<boolean>
  onRegister: (email: string, username: string, password: string) => Promise<boolean>
  error: string | null
}

export function LoginPage({ onLogin, onRegister, error }: Props) {
  const [mode, setMode] = useState<'login' | 'register'>('login')

  // Login fields
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')

  // Register fields
  const [regEmail, setRegEmail] = useState('')
  const [regUsername, setRegUsername] = useState('')
  const [regPassword, setRegPassword] = useState('')
  const [regConfirm, setRegConfirm] = useState('')
  const [localError, setLocalError] = useState<string | null>(null)

  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState<string | null>(null)

  const switchMode = (m: 'login' | 'register') => {
    setMode(m)
    setLocalError(null)
    setSuccess(null)
  }

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setLocalError(null)
    await onLogin(username, password)
    setLoading(false)
  }

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault()
    setLocalError(null)
    setSuccess(null)

    if (regPassword !== regConfirm) {
      setLocalError('Passwords do not match.')
      return
    }
    if (regPassword.length < 8) {
      setLocalError('Password must be at least 8 characters.')
      return
    }

    setLoading(true)
    const ok = await onRegister(regEmail, regUsername, regPassword)
    setLoading(false)

    if (ok) {
      setSuccess('Account created! You can now sign in.')
      setRegEmail('')
      setRegUsername('')
      setRegPassword('')
      setRegConfirm('')
      setTimeout(() => switchMode('login'), 1500)
    }
  }

  const displayError = localError || error

  return (
    <div className="login-page">
      <div className="login-card">

        {/* Logo */}
        <div className="login-logo">
          <span className="logo-pulse" />
          <span className="logo-text">PrintPulse</span>
        </div>
        <p className="login-sub">Faultline Command Center</p>

        {/* Tab toggle */}
        <div className="auth-tabs">
          <button
            className={`auth-tab ${mode === 'login' ? 'auth-tab--active' : ''}`}
            onClick={() => switchMode('login')}
            type="button"
          >
            Sign In
          </button>
          <button
            className={`auth-tab ${mode === 'register' ? 'auth-tab--active' : ''}`}
            onClick={() => switchMode('register')}
            type="button"
          >
            Create Account
          </button>
        </div>

        {/* ── SIGN IN FORM ── */}
        {mode === 'login' && (
          <form onSubmit={handleLogin} className="login-form">
            <label className="field-label">Username</label>
            <input
              className="input"
              type="text"
              autoComplete="username"
              placeholder="your username"
              value={username}
              onChange={e => setUsername(e.target.value)}
              required
            />
            <label className="field-label">Password</label>
            <input
              className="input"
              type="password"
              autoComplete="current-password"
              placeholder="••••••••"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
            />
            {displayError && <div className="login-error">{displayError}</div>}
            <button className="btn btn--primary btn--full" type="submit" disabled={loading}>
              {loading ? 'Signing in…' : 'Sign In'}
            </button>
            <p className="auth-switch">
              No account?{' '}
              <button type="button" className="auth-link" onClick={() => switchMode('register')}>
                Create one
              </button>
            </p>
          </form>
        )}

        {/* ── REGISTER FORM ── */}
        {mode === 'register' && (
          <form onSubmit={handleRegister} className="login-form">
            <label className="field-label">Email</label>
            <input
              className="input"
              type="email"
              autoComplete="email"
              placeholder="you@email.com"
              value={regEmail}
              onChange={e => setRegEmail(e.target.value)}
              required
            />
            <label className="field-label">Username</label>
            <input
              className="input"
              type="text"
              autoComplete="username"
              placeholder="choose a username"
              value={regUsername}
              onChange={e => setRegUsername(e.target.value)}
              required
              minLength={3}
            />
            <label className="field-label">Password</label>
            <input
              className="input"
              type="password"
              autoComplete="new-password"
              placeholder="min. 8 characters"
              value={regPassword}
              onChange={e => setRegPassword(e.target.value)}
              required
              minLength={8}
            />
            <label className="field-label">Confirm Password</label>
            <input
              className="input"
              type="password"
              autoComplete="new-password"
              placeholder="repeat password"
              value={regConfirm}
              onChange={e => setRegConfirm(e.target.value)}
              required
            />
            {displayError && <div className="login-error">{displayError}</div>}
            {success && <div className="login-success">{success}</div>}
            <button className="btn btn--primary btn--full" type="submit" disabled={loading}>
              {loading ? 'Creating account…' : 'Create Account'}
            </button>
            <p className="auth-switch">
              Already have an account?{' '}
              <button type="button" className="auth-link" onClick={() => switchMode('login')}>
                Sign in
              </button>
            </p>
          </form>
        )}

      </div>
    </div>
  )
}
