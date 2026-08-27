import React from 'react'
import { LiveReading } from '../types'
import { FAULT_LABELS, FAULT_COLORS, FAULT_BG, SEVERITY, formatConfidence, formatTime } from '../utils/faultUtils'

interface Props {
  reading: LiveReading | null
  connected: boolean
}

export function LiveFeed({ reading, connected }: Props) {
  const fc = reading?.fault_class ?? 'NORMAL'
  const color = FAULT_COLORS[fc]
  const bg = FAULT_BG[fc]
  const isFault = fc !== 'NORMAL'

  return (
    <div className="panel">
      <div className="panel-header">
        <span className="panel-title">Live Feed</span>
        <span className={`conn-dot ${connected ? 'conn-dot--on' : 'conn-dot--off'}`} title={connected ? 'Connected' : 'Disconnected'} />
      </div>

      {reading ? (
        <>
          <div className="fault-badge" style={{ background: bg, borderColor: color, color }}>
            <span className="fault-badge__label">{FAULT_LABELS[fc]}</span>
            <span className="fault-badge__confidence">{formatConfidence(reading.confidence)}</span>
          </div>

          {isFault && (
            <div className="severity-row" style={{ color }}>
              Severity: <strong>{SEVERITY[fc]}</strong>
            </div>
          )}

          <div className="sensor-grid">
            <SensorCard label="Vibration RMS Z" value={reading.accel_rms_z} unit="g" decimals={4} />
            <SensorCard label="Current RMS" value={reading.current_rms} unit="A" decimals={3} />
            <SensorCard label="Temperature" value={reading.temperature} unit="°C" decimals={1} />
          </div>

          <div className="live-timestamp">
            Last update: {formatTime(reading.received_at)}
          </div>
        </>
      ) : (
        <div className="empty-state">Waiting for first reading…</div>
      )}
    </div>
  )
}

function SensorCard({ label, value, unit, decimals }: {
  label: string; value: number | null; unit: string; decimals: number
}) {
  return (
    <div className="sensor-card">
      <div className="sensor-card__label">{label}</div>
      <div className="sensor-card__value">
        {value !== null ? value.toFixed(decimals) : '—'}
        <span className="sensor-card__unit"> {unit}</span>
      </div>
    </div>
  )
}
