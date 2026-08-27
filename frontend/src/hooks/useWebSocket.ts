import { useEffect, useRef, useState, useCallback } from 'react'
import { LiveReading } from '../types'
import { WS_BASE } from '../config'

const MAX_HISTORY = 60

export function useWebSocket(token: string | null) {
  const wsRef = useRef<WebSocket | null>(null)
  const [latest, setLatest] = useState<LiveReading | null>(null)
  const [history, setHistory] = useState<LiveReading[]>([])
  const [connected, setConnected] = useState(false)

  const push = useCallback((r: LiveReading) => {
    setLatest(r)
    setHistory(prev => {
      const next = [...prev, r]
      return next.length > MAX_HISTORY ? next.slice(-MAX_HISTORY) : next
    })
  }, [])

  useEffect(() => {
    if (!token) return
    const url = `${WS_BASE}/dashboard/ws/live?token=${token}`
    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => setConnected(true)
    ws.onclose = () => setConnected(false)
    ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data)
        if (msg.type === 'live_reading') push(msg as LiveReading)
      } catch {}
    }

    // Keepalive ping every 30s
    const ping = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify({ type: 'pong' }))
    }, 30000)

    return () => { clearInterval(ping); ws.close() }
  }, [token, push])

  return { latest, history, connected }
}
