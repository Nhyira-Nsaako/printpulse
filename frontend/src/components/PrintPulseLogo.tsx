import React from 'react'
import { motion, useReducedMotion } from 'framer-motion'

interface Props {
  width?: number
  height?: number
  color?: string
}

// Vertices of the EKG polyline, used to drive the traveling sweep dot
const PULSE_POINTS = [
  { x: 34, y: 92 },
  { x: 72, y: 92 },
  { x: 82, y: 76 },
  { x: 93, y: 108 },
  { x: 103, y: 92 },
  { x: 166, y: 92 },
]
const PULSE_TIMES = [0, 0.22, 0.36, 0.55, 0.68, 1]

export function PrintPulseLogo({ width = 64, height = 42, color = 'currentColor' }: Props) {
  const reduceMotion = useReducedMotion()
  const draw = (delay: number) =>
    reduceMotion ? { duration: 0 } : { duration: 0.8, delay, ease: [0.16, 1, 0.3, 1] as const }

  return (
    <svg viewBox="0 0 200 130" width={width} height={height} xmlns="http://www.w3.org/2000/svg">
      <defs>
        <filter id="pp-sweep-glow" x="-100%" y="-100%" width="300%" height="300%">
          <feGaussianBlur stdDeviation="2.5" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      <g stroke={color} fill="none" strokeLinecap="round" strokeLinejoin="round">
        {/* Shared central stem — both Ps touch here */}
        <motion.line
          x1="100" y1="12" x2="100" y2="58"
          strokeWidth={9}
          initial={reduceMotion ? false : { pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={draw(0)}
        />
        {/* Left P bowl (mirrored) */}
        <motion.path
          d="M 100 14 A 19 15 0 0 0 79 27 A 19 15 0 0 0 100 40"
          strokeWidth={9}
          initial={reduceMotion ? false : { pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={draw(0.1)}
        />
        {/* Right P bowl (normal orientation) */}
        <motion.path
          d="M 100 14 A 19 15 0 0 1 121 27 A 19 15 0 0 1 100 40"
          strokeWidth={9}
          initial={reduceMotion ? false : { pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={draw(0.1)}
        />

        {/* EKG trace — draws in once, then stays as a dim static baseline */}
        <motion.path
          d="M 34 92 L 72 92 L 82 76 L 93 108 L 103 92 L 166 92"
          strokeWidth={6}
          opacity={0.35}
          initial={reduceMotion ? false : { pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={draw(0.55)}
        />
      </g>

      {/* Traveling sweep dot — the actual "EKG machine" motion */}
      {!reduceMotion && (
        <motion.circle
          r={4}
          fill={color}
          style={{ filter: 'url(#pp-sweep-glow)' }}
          initial={{ opacity: 0 }}
          animate={{
            cx: PULSE_POINTS.map(p => p.x),
            cy: PULSE_POINTS.map(p => p.y),
            opacity: [0, 1, 1, 1, 1, 1, 0],
          }}
          transition={{
            cx: { duration: 1.6, delay: 1.4, repeat: Infinity, ease: 'linear', times: PULSE_TIMES },
            cy: { duration: 1.6, delay: 1.4, repeat: Infinity, ease: 'linear', times: PULSE_TIMES },
            opacity: { duration: 1.6, delay: 1.4, repeat: Infinity, times: [0, 0.05, 0.3, 0.5, 0.7, 0.95, 1] },
          }}
        />
      )}
    </svg>
  )
}
