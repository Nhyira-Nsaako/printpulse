import { useCallback } from 'react'
import { FaultEvent, FaultStats, TrendPoint } from '../types'

const API = '/api'

export function useApi(token: string | null) {
  const headers = useCallback(() => ({
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  }), [token])

  const fetchStats = useCallback(async (): Promise<FaultStats | null> => {
    if (!token) return null
    const res = await fetch(`${API}/faults/stats`, { headers: headers() })
    return res.ok ? res.json() : null
  }, [token, headers])

  const fetchFaults = useCallback(async (page = 1, pageSize = 50, faultClass?: string): Promise<{ items: FaultEvent[], total: number } | null> => {
    if (!token) return null
    const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) })
    if (faultClass && faultClass !== 'ALL') params.append('fault_class', faultClass)
    const res = await fetch(`${API}/faults?${params}`, { headers: headers() })
    return res.ok ? res.json() : null
  }, [token, headers])

  const fetchTrend = useCallback(async (minutes = 60): Promise<TrendPoint[]> => {
    if (!token) return []
    const res = await fetch(`${API}/faults/trend?minutes=${minutes}`, { headers: headers() })
    if (!res.ok) return []
    const data = await res.json()
    return data.points ?? []
  }, [token, headers])

  const acknowledgeFault = useCallback(async (id: number, notes?: string): Promise<boolean> => {
    if (!token) return false
    const res = await fetch(`${API}/faults/${id}/acknowledge`, {
      method: 'POST',
      headers: headers(),
      body: JSON.stringify({ notes }),
    })
    return res.ok
  }, [token, headers])

  const exportCSV = useCallback(async () => {
    if (!token) return
    const res = await fetch(`${API}/faults?page_size=200`, { headers: headers() })
    if (!res.ok) return
    const data = await res.json()
    const events: FaultEvent[] = data.items
    const rows = [
      ['ID', 'Fault Class', 'Confidence', 'Vibration RMS Z', 'Current RMS', 'Temperature', 'Received At', 'Acknowledged'],
      ...events.map(e => [
        e.id, e.fault_class, (e.confidence * 100).toFixed(1) + '%',
        e.accel_rms_z ?? '', e.current_rms ?? '', e.temperature ?? '',
        e.received_at, e.acknowledged ? 'Yes' : 'No',
      ])
    ]
    const csv = rows.map(r => r.join(',')).join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = `printpulse-faults-${Date.now()}.csv`
    a.click(); URL.revokeObjectURL(url)
  }, [token, headers])

  return { fetchStats, fetchFaults, fetchTrend, acknowledgeFault, exportCSV }
}
