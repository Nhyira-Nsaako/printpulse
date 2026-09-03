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

const baseOpts = (title: string) => ({
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
  const pointColors = useMemo(() => history.map(h => FAULT_COLORS[h.fault_class]), [history])

  const vibData = {
    labels,
    datasets: [{
      label: 'Vibration RMS Z (g)',
      data: history.map(h => h.accel_rms_z ?? null),
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

  const currentData = {
    labels,
    datasets: [{
      label: 'Current RMS (A)',
      data: history.map(h => h.current_rms ?? null),
      borderColor: '#8b5cf6',
      backgroundColor: 'rgba(139,92,246,0.06)',
      pointBackgroundColor: pointColors,
      pointRadius: 3,
      pointHoverRadius: 5,
      borderWidth: 1.5,
      fill: true,
      tension: 0.3,
    }],
  }

  const tempData = {
    labels,
    datasets: [{
      label: 'Temperature (°C)',
      data: history.map(h => h.temperature ?? null),
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

  if (history.length === 0) {
    return (
      <div className="panel">
        <div className="panel-header">
          <span className="panel-title">Trend Charts</span>
        </div>
        <div className="empty-state">
          No data yet — charts will populate as readings arrive.
        </div>
      </div>
    )
  }

  return (
    <div className="panel">
      <div className="panel-header">
        <span className="panel-title">Trend Charts</span>
        <span className="panel-sub">
          {history.length} readings · coloured dots = fault class
        </span>
      </div>
      <div className="chart-grid">
        <div className="chart-wrap">
          <Line data={vibData} options={baseOpts('Vibration RMS (Z-axis)')} />
        </div>
        <div className="chart-wrap">
          <Line data={currentData} options={baseOpts('Current Draw (RMS)')} />
        </div>
        <div className="chart-wrap">
          <Line data={tempData} options={baseOpts('Hotend Temperature')} />
        </div>
      </div>
    </div>
  )
}
