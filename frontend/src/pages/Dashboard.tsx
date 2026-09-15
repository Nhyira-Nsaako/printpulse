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
import { FaultEvent, FaultStats, User } from '../types'

interface Props {
  token: string
  user: User | null
  onLogout: () => void
  onUpdateProfile: (patch: Partial<Pick<User, 'alert_email' | 'alert_phone' | 'email_alerts_enabled' | 'sms_alerts_enabled'>>) => void
}

type Tab = 'live' | 'log' | 'settings'

const CALLSIGN = 'PRN-04 · FDM CELL A'

export function Dashboard({ token, user, onLogout, onUpdateProfile }: Props) {
  const { latest, history, connected } = useWebSocket(token)
  const { fetchStats, fetchFaults, acknowledgeFault, exportCSV } = useApi(token)
  const { config, saveConfig, alertActive, checkAndAlert, dismissAlert } = useAlerts()

  const [stats, setStats] = useState<FaultStats | null>(null)
  const [events, setEvents] = useState<FaultEvent[]>([])
  const [filter, setFilter] = useState('ALL')
  const [tab, setTab] = useState<Tab>('live')
  const [darkMode, setDarkMode] = useState(
    () => (localStorage.getItem('pp_theme') ?? 'dark') === 'dark'
  )

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', darkMode ? 'dark' : 'light')
    localStorage.setItem('pp_theme', darkMode ? 'dark' : 'light')
  }, [darkMode])

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

  return (
    <div className="dashboard">
      <header className="header">
        <div className="header-meta">
          <span className="header-callsign">{CALLSIGN}</span>
          <span className={`conn-pill ${connected ? 'conn-pill--on' : 'conn-pill--off'}`}>
            <span className="conn-dot" style={{ background: connected ? '#27AE60' : 'var(--text-muted)', marginLeft: 0 }} />
            {connected ? 'Connected' : 'Offline'}
          </span>
        </div>

        <div className="header-main">
          <div className="header-left">
            <span className="header-title">PRINTPULSE</span>
            <span className="header-sub">Faultline Command Center</span>
          </div>
          <div className="header-right">
            <button className="btn btn--outline" onClick={() => setDarkMode(d => !d)}>
              {darkMode ? 'Light' : 'Dark'}
            </button>
            <button className="btn btn--outline" onClick={onLogout}>
              Sign out
            </button>
          </div>
        </div>

        <nav className="header-nav">
          {(['live', 'log', 'settings'] as Tab[]).map(t => (
            <button
              key={t}
              className={`nav-btn ${tab === t ? 'nav-btn--active' : ''}`}
              onClick={() => setTab(t)}
            >
              {t}
            </button>
          ))}
        </nav>
      </header>

      <AlertBanner
        active={alertActive}
        reading={latest}
        threshold={config.confidence_threshold}
        onDismiss={dismissAlert}
      />

      <StatsBar stats={stats} />

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
          <AlertSettings
            user={user}
            onUpdateProfile={onUpdateProfile}
            config={config}
            onSaveConfig={saveConfig}
          />
        )}
      </main>
    </div>
  )
}
