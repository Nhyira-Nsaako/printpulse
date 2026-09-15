import React, { useState } from 'react'
import { AlertConfig } from '../types'

interface Props {
  config: AlertConfig
  onSave: (c: AlertConfig) => void
}

export function AlertSettings({ config, onSave }: Props) {
  const [local, setLocal] = useState(config)

  const update = (patch: Partial<AlertConfig>) => {
    const next = { ...local, ...patch }
    setLocal(next)
    onSave(next)
  }

  return (
    <>
      <div className="panel settings-section">
        <div className="meta-label">Alert routing</div>
        <div className="settings-heading">Notification channels</div>

        <div className="settings-grid">
          <div className="setting-row">
            <div>
              <div className="setting-row__title">Email alerts</div>
              <div className="setting-row__desc">Dispatch on non-normal class at or above threshold.</div>
            </div>
            <button
              className={`toggle ${local.mechanical_fault ? 'toggle--on' : 'toggle--off'}`}
              onClick={() => update({ mechanical_fault: !local.mechanical_fault })}
            >
              <span className="toggle__knob" />
            </button>
          </div>

          <div className="setting-row">
            <div>
              <div className="setting-row__title">SMS alerts</div>
              <div className="setting-row__desc">Duty-phone path for thermal class only in production.</div>
            </div>
            <button
              className={`toggle ${local.thermal_anomaly ? 'toggle--on' : 'toggle--off'}`}
              onClick={() => update({ thermal_anomaly: !local.thermal_anomaly })}
            >
              <span className="toggle__knob" />
            </button>
          </div>
        </div>
      </div>

      <div className="panel settings-section">
        <div className="meta-label">Classifier gate</div>
        <div className="slider-group" style={{ justifyContent: 'space-between', marginBottom: 8 }}>
          <div className="settings-heading" style={{ marginBottom: 0 }}>Confidence threshold</div>
          <span className="slider-val">{(local.confidence_threshold * 100).toFixed(0)}%</span>
        </div>
        <input
          type="range"
          min={0.5}
          max={0.99}
          step={0.01}
          value={local.confidence_threshold}
          onChange={e => update({ confidence_threshold: parseFloat(e.target.value) })}
          style={{ width: '100%', accentColor: 'var(--text-primary)' }}
        />
        <div className="settings-footnote">
          Banner and routing fire only when posterior ≥ this gate (50–99%). Live class still updates below the gate.
        </div>
      </div>
    </>
  )
}
