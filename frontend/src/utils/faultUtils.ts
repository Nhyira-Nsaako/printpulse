import { FaultClass } from '../types'

export const FAULT_LABELS: Record = {
  NORMAL: 'Normal',
  MECHANICAL_FAULT: 'Mechanical Fault',
  THERMAL_ANOMALY: 'Thermal Anomaly',
}

export const FAULT_COLORS: Record = {
  NORMAL: '#27AE60',
  MECHANICAL_FAULT: '#E67E22',
  THERMAL_ANOMALY: '#C0392B',
}

export const FAULT_BG: Record = {
  NORMAL: '#EAFAF1',
  MECHANICAL_FAULT: '#FEF0E7',
  THERMAL_ANOMALY: '#FDEDEC',
}

export const SEVERITY: Record = {
  NORMAL: 'None',
  MECHANICAL_FAULT: 'High',
  THERMAL_ANOMALY: 'Critical',
}

export function isFault(fc: FaultClass) {
  return fc !== 'NORMAL'
}

export function formatConfidence(c: number) {
  return `${(c * 100).toFixed(1)}%`
}

export function formatTime(iso: string) {
  return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

export function formatDateTime(iso: string) {
  return new Date(iso).toLocaleString()
}
