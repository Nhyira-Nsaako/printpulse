import React, { useEffect } from 'react'
import { useAuth } from './hooks/useAuth'
import { LoginPage } from './pages/LoginPage'
import { Dashboard } from './pages/Dashboard'

export default function App() {
  const { token, user, error, login, register, logout, fetchMe } = useAuth()

  useEffect(() => {
    if (token && !user) fetchMe()
  }, [token])

  if (!token) return <LoginPage onLogin={login} onRegister={register} error={error} />
  return <Dashboard token={token} onLogout={logout} />
}
