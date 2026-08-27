import { useEffect, useRef, useState, useCallback } from 'react'
import mqtt, { MqttClient } from 'mqtt'
import { LiveReading } from '../types'

interface MQTTConfig {
  brokerUrl: string   // e.g. "ws://localhost:9001"
  topic: string       // e.g. "printpulse/status"
  username?: string
  password?: string
}

interface UseMQTTReturn {
  latest: LiveReading | null
  history: LiveReading[]  // rolling 60-window buffer
  connected: boolean
  reconnecting: boolean
}

const MAX_HISTORY = 60

export function useMQTT(config: MQTTConfig, onReading?: (r: LiveReading) => void): UseMQTTReturn {
  const clientRef = useRef<MqttClient | null>(null)
  const [latest, setLatest] = useState<LiveReading | null>(null)
  const [history, setHistory] = useState<LiveReading[]>([])
  const [connected, setConnected] = useState(false)
  const [reconnecting, setReconnecting] = useState(false)

  const handleMessage = useCallback((_topic: string, payload: Buffer) => {
    try {
      const data: LiveReading = JSON.parse(payload.toString())
      setLatest(data)
      setHistory(prev => {
        const next = [...prev, data]
        return next.length > MAX_HISTORY ? next.slice(next.length - MAX_HISTORY) : next
      })
      onReading?.(data)
    } catch (e) {
      console.warn('Invalid MQTT payload', e)
    }
  }, [onReading])

  useEffect(() => {
    const client = mqtt.connect(config.brokerUrl, {
      username: config.username,
      password: config.password,
      reconnectPeriod: 3000,
      connectTimeout: 10000,
    })
    clientRef.current = client

    client.on('connect', () => {
      setConnected(true)
      setReconnecting(false)
      client.subscribe(config.topic)
    })
    client.on('reconnect', () => setReconnecting(true))
    client.on('disconnect', () => { setConnected(false) })
    client.on('error', (e) => console.error('MQTT error', e))
    client.on('message', handleMessage)

    return () => { client.end() }
  }, [config.brokerUrl, config.topic])

  return { latest, history, connected, reconnecting }
}
