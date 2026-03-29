import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell,
} from 'recharts'

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-pg-elevated border border-pg-border rounded-xl px-3 py-2 shadow-xl">
      <p className="text-xs text-slate-500 mb-2">{label}</p>
      {payload.map(p => (
        <div key={p.name} className="flex items-center gap-2 mb-1 last:mb-0">
          <span className="w-2 h-2 rounded-full" style={{ background: p.color }} />
          <span className="text-xs text-slate-400">{p.name}:</span>
          <span className="text-xs font-bold text-white tabular">{p.value}</span>
        </div>
      ))}
    </div>
  )
}

function scoreToColor(score) {
  if (score >= 70) return '#EF4444'
  if (score >= 45) return '#F59E0B'
  return '#10B981'
}

export default function RiskDimensionBars({ dimensions }) {
  return (
    <div>
      <p className="text-xs uppercase tracking-widest text-slate-500 mb-4">Risk by Dimension</p>

      <div className="space-y-4">
        {dimensions.map(dim => (
          <div key={dim.dimension}>
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-sm font-medium text-slate-300">{dim.dimension}</span>
              <div className="flex items-center gap-3">
                <span className="text-[10px] text-slate-500">T2: <span className="text-slate-300 font-semibold tabular">{dim.tier2}</span></span>
                <span className="text-[10px] text-slate-500">T3: <span className="text-slate-300 font-semibold tabular">{dim.tier3}</span></span>
              </div>
            </div>

            {/* Tier-2 bar */}
            <div className="space-y-1.5">
              <div className="flex items-center gap-2">
                <span className="text-[9px] text-accent-blue w-4 shrink-0">T2</span>
                <div className="flex-1 h-2 bg-pg-card rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-700 ease-out"
                    style={{ width: `${dim.tier2}%`, background: scoreToColor(dim.tier2), opacity: 0.8 }}
                  />
                </div>
                <span className="text-[10px] font-semibold tabular text-slate-400 w-6 text-right">{dim.tier2}</span>
              </div>

              {/* Tier-3 bar */}
              <div className="flex items-center gap-2">
                <span className="text-[9px] text-accent-cyan w-4 shrink-0">T3</span>
                <div className="flex-1 h-2 bg-pg-card rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-700 ease-out"
                    style={{ width: `${dim.tier3}%`, background: scoreToColor(dim.tier3), opacity: 0.8 }}
                  />
                </div>
                <span className="text-[10px] font-semibold tabular text-slate-400 w-6 text-right">{dim.tier3}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Color legend */}
      <div className="flex items-center gap-4 mt-4 pt-4 border-t border-pg-border">
        <span className="text-[10px] text-slate-500">Risk scale:</span>
        <span className="flex items-center gap-1 text-[10px] text-risk-low"><span className="w-2 h-2 rounded-full bg-risk-low" /> 0–44 Low</span>
        <span className="flex items-center gap-1 text-[10px] text-risk-med"><span className="w-2 h-2 rounded-full bg-risk-med" /> 45–69 Med</span>
        <span className="flex items-center gap-1 text-[10px] text-risk-high"><span className="w-2 h-2 rounded-full bg-risk-high" /> 70+ High</span>
      </div>
    </div>
  )
}
