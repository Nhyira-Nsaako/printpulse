import React, { useState, useEffect } from 'react'
import { AlertConfig, User } from '../types'

interface Props {
  user: User | null
  onUpdateProfile: (patch: Partial<Pick<User, 'alert_email' | 'alert_phone' | 'email_alerts_enabled' | 'sms_alerts_enabled'>>) => void
  config: AlertConfig
  onSaveConfig: (c: AlertConfig) => void
}

export function AlertSettings({ user, onUpdateProfile, config, onSaveConfig }: Props) {
  const [email, setEmail] = useState(user?.alert_email ?? '')
  const [phone, setPhone] = useState(user?.alert_phone ?? '')

  useEffect(() => {
    setEmail(user?.alert_email ?? '')
    setPhone(user?.alert_phone ?? '')
  }, [user])

  return (
    <>
      <div className="panel settings-section">
        <div className="meta-label">Alert routing</div>
        <div className="settings-heading">Notification channels</div>

        <div className="settings-grid">
          <div className="setting-row">
            <div style={{ flex: 1 }}>
              <div className="setting-row__title" style={{ marginBottom: 6 }}>Email alerts</div>
              <input
                className="input-sm"
                style={{ width: '100%' }}
                placeholder="you@ug.edu.gh"
                value={email}
                onChange={e => setEmail(e.target.value)}
                onBlur={() => onUpdateProfile({ alert_email: email })}
              />
            </div>
            <button
              className={`toggle ${user?.email_alerts_enabled ? 'toggle--on' : 'toggle--off'}`}
              onClick={() => onUpdateProfile({ email_alerts_enabled: !user?.email_alerts_enabled })}
            >
              <span className="toggle__knob" />
            </button>
          </div>

          <div className="setting-row">
            <div style={{ flex: 1 }}>
              <div className="setting-row__title" style={{ marginBottom: 6 }}>SMS alerts</div>
              <input
                className="input-sm"
                style={{ width: '100%' }}
                placeholder="+233 XX XXX XXXX"
                value={phone}
                onChange={e => setPhone(e.target.value)}
                onBlur={() => onUpdateProfile({ alert_phone: phone })}
              />
            </div>
            <button
              className={`toggle ${user?.sms_alerts_enabled ? 'toggle--on' : 'toggle--off'}`}
              onClick={() => onUpdateProfile({ sms_alerts_enabled: !user?.sms_alerts_enabled })}
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
          <span className="slider-val">{(config.confidence_threshold * 100).toFixed(0)}%</span>
        </div>
        <input
          type="range"
          min={0.5}
          max={0.99}
          step={0.01}
          value={config.confidence_threshold}
          onChange={e => onSaveConfig({ ...config, confidence_threshold: parseFloat(e.target.value) })}
          style={{ width: '100%', accentColor: 'var(--text-primary)' }}
        />
      </div>
    </>
  )
}
