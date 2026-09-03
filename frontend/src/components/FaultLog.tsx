import React, { useState } from 'react'
import { FaultEvent } from '../types'
import { FAULT_LABELS, FAULT_COLORS, formatConfidence, formatDateTime } from '../utils/faultUtils'

interface Props {
  events: FaultEvent[]
  onAcknowledge: (id: number, notes?: string) => void
  onExport: () => void
  onFilterChange: (fc: string) => void
  filter: string
}

export function FaultLog({ events, onAcknowledge, onExport, onFilterChange, filter }: Props) {
  const [noteMap, setNoteMap] = useState<Record<number, string>>({})

  return (
    <div className="panel">
      <div className="panel-header">
        <span className="panel-title">Fault Log</span>
        <div className="panel-actions">
          <select
            className="select-sm"
            value={filter}
            onChange={e => onFilterChange(e.target.value)}
          >
            <option value="ALL">All classes</option>
            <option value="NOZZLE_CLOG">Nozzle Clog</option>
            <option value="MOTOR_FAULT">Motor Fault</option>
            <option value="THERMAL_RUNAWAY">Thermal Runaway</option>
          </select>
          <button className="btn btn--sm btn--outline" onClick={onExport}>
            Export CSV
          </button>
        </div>
      </div>

      {events.length === 0 ? (
        <div className="empty-state">No fault events recorded yet.</div>
      ) : (
        <div className="fault-table-wrap">
          <table className="fault-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Class</th>
                <th>Confidence</th>
                <th>Vib RMS Z</th>
                <th>Current</th>
                <th>Temp</th>
                <th>Received</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {events.map(e => (
                <tr key={e.id} className={e.acknowledged ? 'row--ack' : ''}>
                  <td className="mono" style={{ color: 'var(--text-muted)', fontSize: 11 }}>
                    #{e.id}
                  </td>
                  <td>
                    <span
                      className="class-pill"
                      style={{
                        color: FAULT_COLORS[e.fault_class],
                        borderColor: FAULT_COLORS[e.fault_class],
                        background: `${FAULT_COLORS[e.fault_class]}14`,
                      }}
                    >
                      {FAULT_LABELS[e.fault_class]}
                    </span>
                  </td>
                  <td className="mono">{formatConfidence(e.confidence)}</td>
                  <td className="mono">{e.accel_rms_z?.toFixed(4) ?? '—'}</td>
                  <td className="mono">{e.current_rms?.toFixed(3) ?? '—'}</td>
                  <td className="mono">{e.temperature?.toFixed(1) ?? '—'}</td>
                  <td className="timestamp">{formatDateTime(e.received_at)}</td>
                  <td>
                    <span className={`status-pill ${e.acknowledged ? 'status-pill--ack' : 'status-pill--open'}`}>
                      {e.acknowledged ? 'Ack' : 'Open'}
                    </span>
                  </td>
                  <td>
                    {!e.acknowledged && e.fault_class !== 'NORMAL' && (
                      <div className="ack-group">
                        <input
                          className="input-sm"
                          placeholder="Notes…"
                          value={noteMap[e.id] ?? ''}
                          onChange={ev =>
                            setNoteMap(p => ({ ...p, [e.id]: ev.target.value }))
                          }
                        />
                        <button
                          className="btn btn--xs btn--primary"
                          onClick={() => {
                            onAcknowledge(e.id, noteMap[e.id])
                            setNoteMap(p => {
                              const n = { ...p }
                              delete n[e.id]
                              return n
                            })
                          }}
                        >
                          Ack
                        </button>
                      </div>
                    )}
                    {e.notes && (
                      <div className="ack-note">{e.notes}</div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
