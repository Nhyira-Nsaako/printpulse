import React from 'react'
import { LiveReading } from '../types'
import { FAULT_LABELS, FAULT_COLORS, formatConfidence } from '../utils/faultUtils'

interface Props {
  active: boolean
  reading: LiveReading | null
  onDismiss: () => void
}

export function AlertBanner({ active, reading, onDismiss }: Props) {
  if (!active || !reading) return null
  const color = FAULT_COLORS[reading.fault_class]

  return (
    <div className="alert-banner" style={{ borderColor: color, background: `${color}18` }}>
      <div className="alert-banner__icon" style={{ color }}>⚠</div>
      <div className="alert-banner__body">
        <strong style={{ color }}>{FAULT_LABELS[reading.fault_class]} Detected</strong>
        <span> — {formatConfidence(reading.confidence)} confidence. Inspect your printer immediately.</span>
      </div>
      <button className="alert-banner__dismiss" onClick={onDismiss}>✕</button>
    </div>
  )
}
