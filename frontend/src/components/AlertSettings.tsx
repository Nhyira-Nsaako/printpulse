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
      <div className="panel-header"><span className="panel-title">Alert Settings</span></div>
      <div className="settings-grid">
        <label className="setting-row">
          <span>Nozzle Clog alerts</span>
          <input type="checkbox" checked={local.nozzle_clog}
            onChange={e => setLocal(p => ({ ...p, nozzle_clog: e.target.checked }))} />
        </label>
        <label className="setting-row">
          <span>Motor Fault alerts</span>
          <input type="checkbox" checked={local.motor_fault}
            onChange={e => setLocal(p => ({ ...p, motor_fault: e.target.checked }))} />
        </label>
        <label className="setting-row">
          <span>Thermal Runaway alerts</span>
          <input type="checkbox" checked={local.thermal_runaway}
            onChange={e => setLocal(p => ({ ...p, thermal_runaway: e.target.checked }))} />
        </label>
        <label className="setting-row">
          <span>Confidence threshold</span>
          <div className="slider-group">
            <input type="range" min={0.5} max={1} step={0.05}
              value={local.confidence_threshold}
              onChange={e => setLocal(p => ({ ...p, confidence_threshold: parseFloat(e.target.value) }))} />
            <span className="slider-val">{(local.confidence_threshold * 100).toFixed(0)}%</span>
          </div>
        </label>
      </div>
      <button className="btn btn--primary" onClick={handleSave}>
        {saved ? '✓ Saved' : 'Save Settings'}
      </button>
    </div>
  )
}
