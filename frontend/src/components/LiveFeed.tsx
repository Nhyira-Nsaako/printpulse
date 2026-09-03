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
        <span
          className={`conn-dot ${connected ? 'conn-dot--on' : 'conn-dot--off'}`}
          title={connected ? 'Connected' : 'Disconnected'}
        />
      </div>

      {reading ? (
        <>
          {/* Fault status badge */}
          <div
            className="fault-badge"
            style={{ background: bg, borderColor: color, color }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <span
                style={{
                  width: 9, height: 9, borderRadius: '50%',
                  background: color,
                  boxShadow: `0 0 8px ${color}`,
                  flexShrink: 0,
                  animation: 'pulse 2s infinite',
                  display: 'inline-block',
                }}
              />
              <span className="fault-badge__label">{FAULT_LABELS[fc]}</span>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div className="fault-badge__confidence">{formatConfidence(reading.confidence)}</div>
              <div style={{ fontSize: 10, opacity: 0.7, fontFamily: 'var(--font-mono)', marginTop: 2 }}>
                confidence
              </div>
            </div>
          </div>

          {/* Severity row — only for non-Normal */}
          {isFault && (
            <div className="severity-row" style={{ color }}>
              Severity: <strong>{SEVERITY[fc]}</strong>
            </div>
          )}

          {/* Sensor readings */}
          <div className="sensor-grid">
            <SensorCard label="Vibration RMS Z" value={reading.accel_rms_z} unit="g"  decimals={4} />
            <SensorCard label="Current RMS"     value={reading.current_rms}  unit="A"  decimals={3} />
            <SensorCard label="Temperature"     value={reading.temperature}  unit="°C" decimals={1} />
          </div>

          <div className="live-timestamp">
            Last update: {formatTime(reading.received_at)}
          </div>
        </>
      ) : (
        <div className="empty-state">
          <div style={{ fontSize: 28, marginBottom: 10, opacity: 0.3 }}>◎</div>
          Waiting for first reading…
        </div>
      )}
    </div>
  )
}

function SensorCard({ label, value, unit, decimals }: {
  label: string
  value: number | null
  unit: string
  decimals: number
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
