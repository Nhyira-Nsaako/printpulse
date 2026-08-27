import { FaultClass } from '../types'

export const FAULT_LABELS: Record<FaultClass, string> = {
  NORMAL: 'Normal',
  NOZZLE_CLOG: 'Nozzle Clog',
  MOTOR_FAULT: 'Motor Fault',
  THERMAL_RUNAWAY: 'Thermal Runaway',
}

export const FAULT_COLORS: Record<FaultClass, string> = {
  NORMAL: '#27AE60',
  NOZZLE_CLOG: '#F39C12',
  MOTOR_FAULT: '#E67E22',
  THERMAL_RUNAWAY: '#C0392B',
}

export const FAULT_BG: Record<FaultClass, string> = {
  NORMAL: '#EAFAF1',
  NOZZLE_CLOG: '#FEF9E7',
  MOTOR_FAULT: '#FEF0E7',
  THERMAL_RUNAWAY: '#FDEDEC',
}

export const SEVERITY: Record<FaultClass, string> = {
  NORMAL: 'None',
  NOZZLE_CLOG: 'Medium',
  MOTOR_FAULT: 'High',
  THERMAL_RUNAWAY: 'Critical',
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
