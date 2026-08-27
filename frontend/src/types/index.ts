export type FaultClass = 'NORMAL' | 'NOZZLE_CLOG' | 'MOTOR_FAULT' | 'THERMAL_RUNAWAY'

export interface LiveReading {
  fault_class: FaultClass
  confidence: number
  accel_rms_z: number | null
  current_rms: number | null
  temperature: number | null
  received_at: string
  event_id?: number
}

export interface FaultEvent {
  id: number
  fault_class: FaultClass
  confidence: number
  accel_rms_z: number | null
  current_rms: number | null
  temperature: number | null
  esp32_timestamp: number | null
  received_at: string
  alert_sent: boolean
  acknowledged: boolean
  acknowledged_at: string | null
  notes: string | null
}

export interface FaultStats {
  total_events: number
  normal_count: number
  nozzle_clog_count: number
  motor_fault_count: number
  thermal_runaway_count: number
  unacknowledged_faults: number
  last_24h_faults: number
}

export interface TrendPoint {
  received_at: string
  fault_class: FaultClass
  confidence: number
  accel_rms_z: number | null
  current_rms: number | null
  temperature: number | null
}

export interface User {
  id: number
  email: string
  username: string
  is_active: boolean
  created_at: string
  alert_email: string | null
  alert_phone: string | null
  alerts_enabled: boolean
}

export interface AlertConfig {
  nozzle_clog: boolean
  motor_fault: boolean
  thermal_runaway: boolean
  confidence_threshold: number
}
