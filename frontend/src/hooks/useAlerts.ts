import { useRef, useCallback, useState } from 'react'
import { LiveReading, AlertConfig, FaultClass } from '../types'

const DEFAULT_CONFIG: AlertConfig = {
  nozzle_clog: true,
  motor_fault: true,
  thermal_runaway: true,
  confidence_threshold: 0.85,
}

const ALERT_CLASSES: Record<keyof Omit<AlertConfig, 'confidence_threshold'>, FaultClass> = {
  nozzle_clog: 'NOZZLE_CLOG',
  motor_fault: 'MOTOR_FAULT',
  thermal_runaway: 'THERMAL_RUNAWAY',
}

export function useAlerts() {
  const [config, setConfig] = useState<AlertConfig>(() => {
    try { return JSON.parse(localStorage.getItem('pp_alerts') ?? '') }
    catch { return DEFAULT_CONFIG }
  })
  const [alertActive, setAlertActive] = useState(false)
  const audioCtxRef = useRef<AudioContext | null>(null)

  const saveConfig = useCallback((c: AlertConfig) => {
    setConfig(c)
    localStorage.setItem('pp_alerts', JSON.stringify(c))
  }, [])

  const playTone = useCallback((freq: number, duration = 0.3) => {
    if (!audioCtxRef.current) audioCtxRef.current = new AudioContext()
    const ctx = audioCtxRef.current
    const osc = ctx.createOscillator()
    const gain = ctx.createGain()
    osc.connect(gain); gain.connect(ctx.destination)
    osc.frequency.value = freq
    gain.gain.setValueAtTime(0.3, ctx.currentTime)
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration)
    osc.start(); osc.stop(ctx.currentTime + duration)
  }, [])

  const checkAndAlert = useCallback((reading: LiveReading) => {
    const fc = reading.fault_class
    if (fc === 'NORMAL') { setAlertActive(false); return }

    const key = Object.entries(ALERT_CLASSES).find(([, v]) => v === fc)?.[0] as keyof typeof ALERT_CLASSES | undefined
    if (!key || !config[key]) return
    if (reading.confidence < config.confidence_threshold) return

    setAlertActive(true)
    // Tone frequency by severity
    const freq = fc === 'THERMAL_RUNAWAY' ? 880 : fc === 'MOTOR_FAULT' ? 660 : 440
    playTone(freq)
    if (fc === 'THERMAL_RUNAWAY') setTimeout(() => playTone(freq), 400)
  }, [config, playTone])

  const dismissAlert = useCallback(() => setAlertActive(false), [])

  return { config, saveConfig, alertActive, checkAndAlert, dismissAlert }
}
