import React from 'react'
import { LiveReading } from '../types'
import { FAULT_LABELS, formatConfidence } from '../utils/faultUtils'

const FAULT_NOTES: Record<string, string> = {
  MECHANICAL_FAULT: 'Predictive wear signature on vibration channel. Inspect belt/bearing path.',
  THERMAL_ANOMALY: 'Temperature deviation exceeds nominal profile. Check heater and thermistor wiring.',
}

const BANNER_BG: Record<string, string> = {
  MECHANICAL_FAULT: '#E7DAB8',
  THERMAL_ANOMALY: '#F6D8D4',
}
const BANNER_TEXT: Record<string, string> = {
  MECHANICAL_FAULT: '#7A5A18',
  THERMAL_ANOMALY: '#8C2A20',
}

interface Props {
  active: boolean
  reading: LiveReading | null
  threshold: number
  onDismiss: () => void
}

export function AlertBanner({ active, reading, threshold }: Props) {
  if (!active || !reading || reading.fault_class === 'NORMAL') return null

  const bg = BANNER_BG[reading.fault_class]
  const text = BANNER_TEXT[reading.fault_class]

  return (
    <div className="alert-banner" style={{ background: bg }}>
      <div className="alert-banner__headline" style={{ color: text }}>
        Active fault · {FAULT_LABELS[reading.fault_class]} · confidence {formatConfidence(reading.confidence)} (threshold {Math.round(threshold * 100)}%)
      </div>
      <div className="alert-banner__note" style={{ color: text }}>
        {FAULT_NOTES[reading.fault_class]}
      </div>
    </div>
  )
}
