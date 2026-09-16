import React, { useMemo } from 'react'
import { Line } from 'react-chartjs-2'
import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement,
  LineElement, Title, Tooltip, Legend, Filler,
} from 'chart.js'
import { LiveReading } from '../types'
import { FAULT_COLORS, formatTime } from '../utils/faultUtils'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler)

interface Props { history: LiveReading[] }

/**
 * Compute a padded min/max from the actual data instead of trusting
 * Chart.js's auto-scale, which doesn't zoom in well for small-magnitude
 * series like vibration (values ~0.005-0.02) sitting alongside sparse
 * or null readings.
 */
function computeRange(values: (number | null | undefined)[]) {
  const nums = values.filter((v): v is number => v !== null && v !== undefined)
  if (nums.length === 0) return { min: 0, max: 1 }

  const dataMin = Math.min(...nums)
  const dataMax = Math.max(...nums)
  const span = dataMax - dataMin

  // Flat/near-flat series (e.g. steady idle vibration) still need some
  // visible headroom rather than collapsing to a zero-height line.
  const padding = span > 0 ? span * 0.15 : Math.max(Math.abs(dataMax) * 0.1, 0.01)

  return {
    min: Math.max(0, dataMin - padding),
    max: dataMax + padding,
  }
}

const baseOpts = (title: string, range: { min: number; max: number }) => ({
  responsive: true,
  maintainAspectRatio: false,
  animation: { duration: 200 } as const,
  plugins: {
    legend: { display: false },
    title: {
      display: true,
      text: title,
      color: '#8890a8',
      font: { size: 11, family: 'Geist Mono, JetBrains Mono, monospace' },
      padding: { bottom: 8 },
    },
    tooltip: {
      backgroundColor: '#161820',
      borderColor: '#1e2130',
      borderWidth: 1,
      titleColor: '#f0f2f8',
      bodyColor: '#8890a8',
      titleFont: { family: 'Geist Mono, monospace', size: 11 },
      bodyFont: { family: 'Geist Mono, monospace', size: 11 },
    },
  },
  scales: {
    x: {
      ticks: {
        color: '#4a5068',
        maxTicksLimit: 6,
        font: { size: 9, family: 'Geist Mono, monospace' },
      },
      grid: { color: '#1e2130' },
      border: { color: '#1e2130' },
    },
    y: {
      min: range.min,
      max: range.max,
      ticks: {
        color: '#4a5068',
        font: { size: 9, family: 'Geist Mono, monospace' },
      },
      grid: { color: '#1e2130' },
      border: { color: '#1e2130' },
    },
  },
})

export function TrendCharts({ history }: Props) {
  const labels = useMemo(() => history.map(h => formatTime(h.received_at)), [history])
  const pointColors = useMemo(() => history.map(h => FAULT_COLORS[h.fault_class] ?? '#8890a8'), [history])

  const vibValues = useMemo(() => history.map(h => h.accel_rms_z), [history])
  const nozzleValues = useMemo(() => history.map(h => h.nozzle_temp), [history])
  const bedValues = useMemo(() => history.map(h => h.bed_temp), [history])

  const vibRange = useMemo(() => computeRange(vibValues), [vibValues])
  const nozzleRange = useMemo(() => computeRange(nozzleValues), [nozzleValues])
  const bedRange = useMemo(() => computeRange(bedValues), [bedValues])

  const vibData = {
    labels,
    datasets: [{
      label: 'Vibration RMS Z (g)',
      data: vibValues.map(v => v ?? null),
      borderColor: '#3b82f6',
      backgroundColor: 'rgba(59,130,246,0.06)',
      pointBackgroundColor: pointColors,
      pointRadius: 3,
      pointHoverRadius: 5,
      borderWidth: 1.5,
      fill: true,
      tension: 0.3,
    }],
  }

  const nozzleTempData = {
    labels,
    datasets: [{
      label: 'Nozzle Temp (°C)',
      data: nozzleValues.map(v => v ?? null),
      borderColor: '#ef4444',
      backgroundColor: 'rgba(239,68,68,0.06)',
      pointBackgroundColor: pointColors,
      pointRadius: 3,
      pointHoverRadius: 5,
      borderWidth: 1.5,
      fill: true,
      tension: 0.3,
    }],
  }

  const bedTempData = {
    labels,
    datasets: [{
      label: 'Bed Temp (°C)',
      data: bedValues.map(v => v ?? null),
      borderColor: '#f59e0b',
      backgroundColor: 'rgba(245,158,11,0.06)',
      pointBackgroundColor: pointColors,
      pointRadius: 3,
      pointHoverRadius: 5,
      borderWidth: 1.5,
      fill: true,
      tension: 0.3,
    }],
  }

  if (history.length === 0) {
    return (
      <div>
        <h3>Trend Charts</h3>
        <p>No data yet — charts will populate as readings arrive.</p>
      </div>
    )
  }

  return (
    <div>
      <h3>Trend Charts</h3>
      <p>{history.length} readings · coloured dots = fault class</p>

      <div style={{ height: 200 }}>
        <Line data={vibData} options={baseOpts('Vibration RMS Z (g)', vibRange)} />
      </div>
      <div style={{ height: 200 }}>
        <Line data={nozzleTempData} options={baseOpts('Nozzle Temp (°C)', nozzleRange)} />
      </div>
      <div style={{ height: 200 }}>
        <Line data={bedTempData} options={baseOpts('Bed Temp (°C)', bedRange)} />
      </div>
    </div>
  )
}
