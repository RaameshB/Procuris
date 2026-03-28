import { useEffect, useState } from 'react'

const ZONES = [
  { label: 'Low',    from: 0,   to: 33,  color: '#10B981' },
  { label: 'Medium', from: 33,  to: 66,  color: '#F59E0B' },
  { label: 'High',   from: 66,  to: 100, color: '#EF4444' },
]

function getZoneColor(pct) {
  if (pct >= 66) return '#EF4444'
  if (pct >= 33) return '#F59E0B'
  return '#10B981'
}

export default function DependencyExposureBar({ exposure }) {
  const [animated, setAnimated] = useState(false)
  const color = getZoneColor(exposure)

  useEffect(() => {
    setAnimated(false)
    const t = setTimeout(() => setAnimated(true), 100)
    return () => clearTimeout(t)
  }, [exposure])

  return (
    <div>
      {/* Header */}
      <div className="flex items-end justify-between mb-3">
        <div>
          <p className="text-xs uppercase tracking-widest text-slate-500 mb-1">Dependency Exposure</p>
          <div className="flex items-baseline gap-2">
            <span className="text-4xl font-bold tabular text-white">{exposure}</span>
            <span className="text-lg text-slate-400 font-medium">%</span>
          </div>
        </div>
        <p className="text-xs text-slate-500 pb-1 text-right leading-relaxed">
          Upstream concentration<br />in high-risk ecosystems
        </p>
      </div>

      {/* Segmented track */}
      <div className="relative h-4 rounded-full overflow-hidden bg-pg-card border border-pg-border flex">
        {ZONES.map(z => {
          const width = z.to - z.from
          const filled = Math.max(0, Math.min(exposure - z.from, width))
          const pct = (filled / width) * 100
          return (
            <div key={z.label} className="relative overflow-hidden" style={{ width: `${width}%` }}>
              <div className="absolute inset-0 opacity-10" style={{ background: z.color }} />
              <div
                className="h-full rounded-sm transition-all duration-700 ease-out"
                style={{
                  width:  animated ? `${pct}%` : '0%',
                  background: z.color,
                  opacity: 0.85,
                }}
              />
            </div>
          )
        })}

        {/* Needle */}
        <div
          className="absolute top-0 bottom-0 w-0.5 rounded-full bg-white shadow-lg transition-all duration-700 ease-out"
          style={{ left: animated ? `calc(${exposure}% - 1px)` : '0%' }}
        />
      </div>

      {/* Zone labels */}
      <div className="flex justify-between mt-1.5">
        <span className="text-[10px] text-risk-low">Low (0–33)</span>
        <span className="text-[10px] text-risk-med">Medium (33–66)</span>
        <span className="text-[10px] text-risk-high">High (66–100)</span>
      </div>

      {/* Interpretation */}
      <p className="text-xs text-slate-500 mt-3 leading-relaxed border-t border-pg-border pt-3">
        {exposure >= 66
          ? 'Critical concentration — majority of upstream dependencies inferred in high-risk supply ecosystems.'
          : exposure >= 33
          ? 'Moderate concentration — notable upstream exposure to medium-risk supplier networks.'
          : 'Well-distributed — upstream dependencies spread across lower-risk supplier ecosystems.'}
      </p>
    </div>
  )
}
