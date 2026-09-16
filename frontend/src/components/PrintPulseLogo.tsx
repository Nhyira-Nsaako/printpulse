import React from 'react'
import { motion, useReducedMotion } from 'framer-motion'

interface Props {
  width?: number
  height?: number
  color?: string
}

/**
 * Two Ps sharing a fused central stem (mirrored ambigram — left bowl
 * curves left, right bowl curves right), with a small EKG strip beneath.
 * Single color via `color`/currentColor so it can never clash with theme.
 * Draws in on mount; the EKG strip loops a soft heartbeat flicker after.
 * Respects prefers-reduced-motion.
 */
export function PrintPulseLogo({ width = 64, height = 42, color = 'currentColor' }: Props) {
  const reduceMotion = useReducedMotion()
  const draw = (delay: number) =>
    reduceMotion ? { duration: 0 } : { duration: 0.8, delay, ease: [0.16, 1, 0.3, 1] as const }

  return (
    <svg viewBox="0 0 200 130" width={width} height={height} xmlns="http://www.w3.org/2000/svg">
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
        {/* EKG strip beneath */}
        <motion.path
          d="M 34 92 L 72 92 L 82 76 L 93 108 L 103 92 L 166 92"
          strokeWidth={6}
          initial={reduceMotion ? false : { pathLength: 0 }}
          animate={reduceMotion ? { pathLength: 1 } : { pathLength: 1, opacity: [1, 0.5, 1] }}
          transition={
            reduceMotion
              ? { duration: 0 }
              : { pathLength: draw(0.55), opacity: { duration: 1.8, delay: 1.4, repeat: Infinity, ease: 'easeInOut' } }
          }
        />
      </g>
    </svg>
  )
}
