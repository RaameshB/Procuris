import { useEffect, useState } from 'react'
import { useCountUp } from '../../../hooks/useCountUp'

const CX = 110
const CY = 110
const R = 80
const STROKE = 13
const START_DEG = 135
const SWEEP = 270
const CIRCUMFERENCE = (SWEEP / 360) * (2 * Math.PI * R)

function polar(cx, cy, r, deg) {
  const rad = (deg * Math.PI) / 180
  return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) }
}

function arc(cx, cy, r, startDeg, endDeg) {
  const s = polar(cx, cy, r, startDeg)
  const e = polar(cx, cy, r, endDeg)
  const large = endDeg - startDeg > 180 ? 1 : 0
  return `M ${s.x.toFixed(2)} ${s.y.toFixed(2)} A ${r} ${r} 0 ${large} 1 ${e.x.toFixed(2)} ${e.y.toFixed(2)}`
}

const RISK_COLORS = {
  High:   { stroke: '#EF4444', glow: 'rgba(239,68,68,0.3)',   label: 'text-risk-high',  bg: 'bg-risk-high/10',  border: 'border-risk-high/25' },
  Medium: { stroke: '#F59E0B', glow: 'rgba(245,158,11,0.3)',  label: 'text-risk-med',   bg: 'bg-risk-med/10',   border: 'border-risk-med/25'  },
  Low:    { stroke: '#10B981', glow: 'rgba(16,185,129,0.3)',  label: 'text-risk-low',   bg: 'bg-risk-low/10',   border: 'border-risk-low/25'  },
}

export default function RiskScoreGauge({ score, riskLevel }) {
  const [animated, setAnimated] = useState(false)
  const displayScore = useCountUp(score, 1400)
  const c = RISK_COLORS[riskLevel] || RISK_COLORS.Medium

  const trackPath = arc(CX, CY, R, START_DEG, START_DEG + SWEEP)
  const valuePath = arc(CX, CY, R, START_DEG, START_DEG + (score / 100) * SWEEP)

  const dashArray  = CIRCUMFERENCE
  const dashOffset = animated
    ? CIRCUMFERENCE * (1 - score / 100)
    : CIRCUMFERENCE

  useEffect(() => {
    setAnimated(false)
    const t = setTimeout(() => setAnimated(true), 80)
    return () => clearTimeout(t)
  }, [score])

  // Tick marks at 0%, 25%, 50%, 75%, 100%
  const ticks = [0, 25, 50, 75, 100].map(pct => {
    const deg = START_DEG + (pct / 100) * SWEEP
    const inner = polar(CX, CY, R - 10, deg)
    const outer = polar(CX, CY, R + 4, deg)
    return { inner, outer, pct }
  })

  return (
    <div className="flex flex-col items-center">
      <div className="relative">
        <svg width={220} height={200} viewBox={`0 0 ${CX * 2} ${CY * 2 - 20}`} className="overflow-visible">
          <defs>
            <filter id="gauge-glow">
              <feGaussianBlur stdDeviation="5" result="blur" />
              <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
            </filter>
          </defs>

          {/* Background track */}
          <path
            d={trackPath}
            fill="none"
            stroke="#1C2A3E"
            strokeWidth={STROKE}
            strokeLinecap="round"
          />

          {/* Glow layer */}
          <path
            d={valuePath}
            fill="none"
            stroke={c.stroke}
            strokeWidth={STROKE + 8}
            strokeLinecap="round"
            opacity={0.15}
            filter="url(#gauge-glow)"
            style={{
              strokeDasharray:  dashArray,
              strokeDashoffset: dashOffset,
              transition: 'stroke-dashoffset 1.4s cubic-bezier(0.33, 1, 0.68, 1)',
            }}
          />

          {/* Value arc */}
          <path
            d={valuePath}
            fill="none"
            stroke={c.stroke}
            strokeWidth={STROKE}
            strokeLinecap="round"
            style={{
              strokeDasharray:  dashArray,
              strokeDashoffset: dashOffset,
              transition: 'stroke-dashoffset 1.4s cubic-bezier(0.33, 1, 0.68, 1)',
            }}
          />

          {/* Tick marks */}
          {ticks.map(({ inner, outer, pct }) => (
            <line
              key={pct}
              x1={inner.x} y1={inner.y}
              x2={outer.x} y2={outer.y}
              stroke="#243550"
              strokeWidth={1.5}
              strokeLinecap="round"
            />
          ))}

          {/* Center: score */}
          <text
            x={CX} y={CY - 4}
            textAnchor="middle"
            dominantBaseline="middle"
            fill="white"
            fontSize="38"
            fontWeight="800"
            fontFamily="Inter, system-ui, sans-serif"
            style={{ fontVariantNumeric: 'tabular-nums' }}
          >
            {displayScore}
          </text>

          {/* Center: /100 label */}
          <text
            x={CX} y={CY + 22}
            textAnchor="middle"
            fill="#64748B"
            fontSize="11"
            fontFamily="Inter, system-ui, sans-serif"
          >
            / 100 risk score
          </text>
        </svg>
      </div>

      {/* Risk level badge */}
      <span className={`inline-flex items-center gap-1.5 px-4 py-1.5 rounded-full border text-sm font-semibold ${c.label} ${c.bg} ${c.border} -mt-1`}>
        <span className="w-2 h-2 rounded-full" style={{ backgroundColor: c.stroke }} />
        {riskLevel} Risk
      </span>
    </div>
  )
}
