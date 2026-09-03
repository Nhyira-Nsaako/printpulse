import { useState, useCallback } from 'react'
import { User } from '../types'
import { API_BASE as API } from '../config'

export function useAuth() {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('pp_token'))
  const [user, setUser] = useState<User | null>(null)
  const [error, setError] = useState<string | null>(null)

  const login = useCallback(async (username: string, password: string) => {
    setError(null)
    const form = new URLSearchParams({ username, password })
    const res = await fetch(`${API}/auth/login`, { method: 'POST', body: form })
    if (!res.ok) { setError('Invalid username or password.'); return false }
    const data = await res.json()
    localStorage.setItem('pp_token', data.access_token)
    setToken(data.access_token)
    return true
  }, [])

  const register = useCallback(async (email: string, username: string, password: string) => {
    setError(null)
    const res = await fetch(`${API}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, username, password }),
    })
    if (!res.ok) {
      const data = await res.json().catch(() => ({}))
      setError(data.detail ?? 'Registration failed. Please try again.')
      return false
    }
    return true
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('pp_token')
    setToken(null)
    setUser(null)
  }, [])

  const fetchMe = useCallback(async (t?: string) => {
    const tok = t ?? token
    if (!tok) return
    const res = await fetch(`${API}/auth/me`, {
      headers: { Authorization: `Bearer ${tok}` },
    })
    if (res.ok) setUser(await res.json())
  }, [token])

  return { token, user, error, login, register, logout, fetchMe }
}
