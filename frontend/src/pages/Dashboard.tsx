import React, { useEffect, useState, useCallback } from 'react'
import { LiveFeed } from '../components/LiveFeed'
import { TrendCharts } from '../components/TrendCharts'
import { FaultLog } from '../components/FaultLog'
import { StatsBar } from '../components/StatsBar'
import { AlertBanner } from '../components/AlertBanner'
import { AlertSettings } from '../components/AlertSettings'
import { useWebSocket } from '../hooks/useWebSocket'
import { useApi } from '../hooks/useApi'
import { useAlerts } from '../hooks/useAlerts'
import { FaultEvent, FaultStats, LiveReading } from '../types'
import { FAULT_COLORS } from '../utils/faultUtils'

interface Props {
  token: string
  onLogout: () => void
}

type Tab = 'live' | 'log' | 'settings'

export function Dashboard({ token, onLogout }: Props) {
  const { latest, history, connected } = useWebSocket(token)
  const { fetchStats, fetchFaults, acknowledgeFault, exportCSV } = useApi(token)
  const { config, saveConfig, alertActive, checkAndAlert, dismissAlert } = useAlerts()

  const [stats, setStats] = useState<FaultStats | null>(null)
  const [events, setEvents] = useState<FaultEvent[]>([])
  const [filter, setFilter] = useState('ALL')
  const [tab, setTab] = useState<Tab>('live')
  const [darkMode, setDarkMode] = useState(() => localStorage.getItem('pp_theme') === 'dark')

  // Apply theme
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', darkMode ? 'dark' : 'light')
    localStorage.setItem('pp_theme', darkMode ? 'dark' : 'light')
  }, [darkMode])

  // Load stats on mount and after each new reading
  const refreshStats = useCallback(async () => {
    const s = await fetchStats()
    if (s) setStats(s)
  }, [fetchStats])

  const refreshFaults = useCallback(async () => {
    const data = await fetchFaults(1, 100, filter === 'ALL' ? undefined : filter)
    if (data) setEvents(data.items)
  }, [fetchFaults, filter])

  useEffect(() => { refreshStats(); refreshFaults() }, [])
  useEffect(() => { refreshFaults() }, [filter])

  // Check alerts on every new reading
  useEffect(() => {
    if (latest) {
      checkAndAlert(latest)
      refreshStats()
    }
  }, [latest])

  const handleAcknowledge = async (id: number, notes?: string) => {
    const ok = await acknowledgeFault(id, notes)
    if (ok) refreshFaults()
  }

  // Header colour pulse on fault
  const headerColor = latest ? FAULT_COLORS[latest.fault_class] : 'var(--accent)'

  return (
    <div className="dashboard">
      {/* ── Header ── */}
      <header className="header" style={{ borderBottomColor: alertActive ? headerColor : 'var(--border)' }}>
        <div className="header-left">
          <span className="logo-pulse" style={{ background: headerColor }} />
          <span className="header-title">PrintPulse</span>
          <span className="header-sub">Faultline Command Center</span>
        </div>
        <nav className="header-nav">
          {(['live', 'log', 'settings'] as Tab[]).map(t => (
            <button
              key={t}
              className={`nav-btn ${tab === t ? 'nav-btn--active' : ''}`}
              onClick={() => setTab(t)}
            >
              {t === 'live' ? '⚡ Live' : t === 'log' ? '📋 Fault Log' : '⚙ Settings'}
            </button>
          ))}
        </nav>
        <div className="header-right">
          <button className="icon-btn" title="Toggle theme" onClick={() => setDarkMode(d => !d)}>
            {darkMode ? '☀' : '☾'}
          </button>
          <button className="btn btn--sm btn--outline" onClick={onLogout}>Sign out</button>
        </div>
      </header>

      {/* ── Alert Banner ── */}
      <AlertBanner active={alertActive} reading={latest} onDismiss={dismissAlert} />

      {/* ── Stats Bar ── */}
      <StatsBar stats={stats} />

      {/* ── Main content ── */}
      <main className="main">
        {tab === 'live' && (
          <>
            <LiveFeed reading={latest} connected={connected} />
            <TrendCharts history={history} />
          </>
        )}
        {tab === 'log' && (
          <FaultLog
            events={events}
            onAcknowledge={handleAcknowledge}
            onExport={exportCSV}
            onFilterChange={setFilter}
            filter={filter}
          />
        )}
        {tab === 'settings' && (
          <AlertSettings config={config} onSave={saveConfig} />
        )}
      </main>
    </div>
  )
}
