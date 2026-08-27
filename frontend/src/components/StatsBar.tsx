import React from 'react'
import { FaultStats } from '../types'
import { FAULT_COLORS } from '../utils/faultUtils'

interface Props { stats: FaultStats | null }

export function StatsBar({ stats }: Props) {
  if (!stats) return null

  const items = [
    { label: 'Total Events', value: stats.total_events, color: 'var(--text-primary)' },
    { label: 'Normal', value: stats.normal_count, color: FAULT_COLORS.NORMAL },
    { label: 'Nozzle Clog', value: stats.nozzle_clog_count, color: FAULT_COLORS.NOZZLE_CLOG },
    { label: 'Motor Fault', value: stats.motor_fault_count, color: FAULT_COLORS.MOTOR_FAULT },
    { label: 'Thermal Runaway', value: stats.thermal_runaway_count, color: FAULT_COLORS.THERMAL_RUNAWAY },
    { label: 'Unacknowledged', value: stats.unacknowledged_faults, color: '#E74C3C' },
    { label: 'Last 24 h', value: stats.last_24h_faults, color: 'var(--text-secondary)' },
  ]

  return (
    <div className="stats-bar">
      {items.map(item => (
        <div key={item.label} className="stat-card">
          <div className="stat-card__value" style={{ color: item.color }}>{item.value}</div>
          <div className="stat-card__label">{item.label}</div>
        </div>
      ))}
    </div>
  )
}
