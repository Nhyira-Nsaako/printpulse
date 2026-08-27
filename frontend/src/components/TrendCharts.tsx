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
    title: { display: true, text: title, color: 'var(--text-secondary)', font: { size: 12, family: 'Plus Jakarta Sans' } },
  },
  scales: {
    x: { ticks: { color: 'var(--text-muted)', maxTicksLimit: 8, font: { size: 10 } }, grid: { color: 'var(--border)' } },
    y: { ticks: { color: 'var(--text-muted)', font: { size: 10 } }, grid: { color: 'var(--border)' } },
  },
})

export function TrendCharts({ history }: Props) {
  const labels = useMemo(() => history.map(h => formatTime(h.received_at)), [history])

  const pointColors = useMemo(
    () => history.map(h => FAULT_COLORS[h.fault_class]),
    [history]
  )

  const vibData = {
    labels,
    datasets: [{
      label: 'Vibration RMS Z (g)',
      data: history.map(h => h.accel_rms_z ?? null),
      borderColor: '#2C6FAC', backgroundColor: 'rgba(44,111,172,0.08)',
      pointBackgroundColor: pointColors,
      pointRadius: 3, borderWidth: 1.5, fill: true, tension: 0.3,
    }],
  }

  const currentData = {
    labels,
    datasets: [{
      label: 'Current RMS (A)',
      data: history.map(h => h.current_rms ?? null),
      borderColor: '#534AB7', backgroundColor: 'rgba(83,74,183,0.08)',
      pointBackgroundColor: pointColors,
      pointRadius: 3, borderWidth: 1.5, fill: true, tension: 0.3,
    }],
  }

  const tempData = {
    labels,
    datasets: [{
      label: 'Temperature (°C)',
      data: history.map(h => h.temperature ?? null),
      borderColor: '#C0392B', backgroundColor: 'rgba(192,57,43,0.08)',
      pointBackgroundColor: pointColors,
      pointRadius: 3, borderWidth: 1.5, fill: true, tension: 0.3,
    }],
  }

  if (history.length === 0) {
    return (
      <div className="panel">
        <div className="panel-header"><span className="panel-title">Trend Charts</span></div>
        <div className="empty-state">No data yet — charts will populate as readings arrive.</div>
      </div>
    )
  }

  return (
    <div className="panel">
      <div className="panel-header">
        <span className="panel-title">Trend Charts</span>
        <span className="panel-sub">{history.length} readings · coloured dots = fault class</span>
      </div>
      <div className="chart-grid">
        <div className="chart-wrap"><Line data={vibData} options={baseOpts('Vibration RMS (Z-axis)')} /></div>
        <div className="chart-wrap"><Line data={currentData} options={baseOpts('Current Draw (RMS)')} /></div>
        <div className="chart-wrap"><Line data={tempData} options={baseOpts('Hotend Temperature')} /></div>
      </div>
    </div>
  )
}
