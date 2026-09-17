import React, { useState } from 'react'
import { PrintPulseLogo } from '../components/PrintPulseLogo'

interface Props {
  onLogin: (username: string, password: string) => Promise<boolean>
  onRegister: (email: string, username: string, password: string) => Promise<boolean>
  error: string | null
}

export function LoginPage({ onLogin, onRegister, error }: Props) {
  const [tab, setTab] = useState<'signin' | 'signup'>('signin')
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [signupSuccess, setSignupSuccess] = useState(false)

  const switchTab = (t: 'signin' | 'signup') => {
    setTab(t)
    setSignupSuccess(false)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      if (tab === 'signin') {
        await onLogin(username, password)
      } else {
        const ok = await onRegister(email, username, password)

        if (ok) {
          setSignupSuccess(true)
          setTab('signin')
          setPassword('')
        }
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-page">

      {/* Background */}
      <div className="login-bg">
        <img
          src="https://source.unsplash.com/1600x1200/?3d-printer,fdm-printer"
          alt=""
          className="login-bg__img"
        />
        <div className="login-bg__overlay" />
      </div>

      {/* Login card */}
      <div className="login-card">

        <div className="login-logo" style={{ gap: 8 }}>
          <PrintPulseLogo
            width={64}
            height={42}
            color="var(--text-primary)"
          />

          <span className="logo-text">PrintPulse</span>
        </div>

        <p className="login-sub">Faultline Command Center</p>

        <div className="auth-tabs">
          <button
            type="button"
            className={`auth-tab ${
              tab === 'signin' ? 'auth-tab--active' : ''
            }`}
            onClick={() => switchTab('signin')}
          >
            Sign In
          </button>

          <button
            type="button"
            className={`auth-tab ${
              tab === 'signup' ? 'auth-tab--active' : ''
            }`}
            onClick={() => switchTab('signup')}
          >
            Create Account
          </button>
        </div>

        {signupSuccess && (
          <div
            className="login-success"
            style={{ marginBottom: 12 }}
          >
            Account created — sign in below.
          </div>
        )}

        <form onSubmit={handleSubmit} className="login-form">

          {tab === 'signup' && (
            <>
              <label className="field-label">Email</label>

              <input
                className="input"
                type="email"
                autoComplete="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                required
              />
            </>
          )}

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
            autoComplete={
              tab === 'signin'
                ? 'current-password'
                : 'new-password'
            }
            value={password}
            onChange={e => setPassword(e.target.value)}
            required
          />

          {error && (
            <div className="login-error">
              {error}
            </div>
          )}

          <button
            className="btn btn--primary btn--full"
            type="submit"
            disabled={loading}
          >
            {loading
              ? tab === 'signin'
                ? 'Signing in…'
                : 'Creating account…'
              : tab === 'signin'
                ? 'Sign in'
                : 'Create account'}
          </button>

        </form>
      </div>
    </div>
  )
}

