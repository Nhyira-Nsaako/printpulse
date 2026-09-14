import React, { useState } from 'react'
import { AlertConfig } from '../types'

interface Props {
  config: AlertConfig
  onSave: (c: AlertConfig) => void
}

export function AlertSettings({ config, onSave }: Props) {
  const [local, setLocal] = useState(config)
  const [saved, setSaved] = useState(false)

  const handleSave = () => {
    onSave(local)
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  return (
    <div className="panel">
      <div className="panel-header">
        <span className="panel-title">Alert Settings</span>
      </div>

      <div className="settings-grid">
        <label className="setting-row">
          <span>Mechanical Fault alerts</span>
          <input
            type="checkbox"
            checked={local.mechanical_fault}
            onChange={e => setLocal(p => ({ ...p, mechanical_fault: e.target.checked }))}
            style={{ accentColor: 'var(--accent)', width: 16, height: 16, cursor: 'pointer' }}
          />
        </label>

        <label className="setting-row">
          <span>Thermal Anomaly alerts</span>
          <input
            type="checkbox"
            checked={local.thermal_anomaly}
            onChange={e => setLocal(p => ({ ...p, thermal_anomaly: e.target.checked }))}
            style={{ accentColor: 'var(--accent)', width: 16, height: 16, cursor: 'pointer' }}
          />
        </label>

        <label className="setting-row">
          <span>Confidence threshold</span>
          <div className="slider-group">
            <input
              type="range"
              min={0.5}
              max={1}
              step={0.05}
              value={local.confidence_threshold}
              onChange={e =>
                setLocal(p => ({ ...p, confidence_threshold: parseFloat(e.target.value) }))
              }
              style={{ accentColor: 'var(--accent)', width: 140, cursor: 'pointer' }}
            />
            <span className="slider-val">
              {(local.confidence_threshold * 100).toFixed(0)}%
            </span>
          </div>
        </label>
      </div>

      <button className="btn btn--primary" onClick={handleSave}>
        {saved ? '✓ Saved' : 'Save Settings'}
      </button>
    </div>
  )
}
