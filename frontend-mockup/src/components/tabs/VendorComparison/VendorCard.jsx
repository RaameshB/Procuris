import { AreaChart, Area, ResponsiveContainer, Tooltip } from 'recharts'
import RiskBadge from '../../shared/RiskBadge'

const RISK_COLORS = {
  High:   { stroke: '#EF4444', fill: 'rgba(239,68,68,0.15)',   ring: 'ring-risk-high/30' },
  Medium: { stroke: '#F59E0B', fill: 'rgba(245,158,11,0.15)',  ring: 'ring-risk-med/30'  },
  Low:    { stroke: '#10B981', fill: 'rgba(16,185,129,0.15)',  ring: 'ring-risk-low/30'  },
}

const DIRECTION_ICONS = {
  Increasing: '↑',
  Stable:     '→',
  Decreasing: '↓',
}

const DIRECTION_COLORS = {
  Increasing: 'text-risk-high',
  Stable:     'text-risk-med',
  Decreasing: 'text-risk-low',
}

export default function VendorCard({ vendor, isSelected, onClick, label }) {
  const rc = RISK_COLORS[vendor.riskLevel] || RISK_COLORS.Medium

  return (
    <button
      onClick={onClick}
      className={`w-full text-left bg-pg-card rounded-2xl border transition-all duration-200 p-5
        ${isSelected
          ? 'border-accent-blue/40 ring-1 ring-accent-blue/20 shadow-[0_0_24px_rgba(59,130,246,0.12)]'
          : 'border-pg-border hover:border-pg-muted'
        }`}
    >
      {/* Top bar */}
      <div className="flex items-start justify-between mb-4">
        <div>
          {label && (
            <p className="text-[10px] uppercase tracking-widest text-slate-600 mb-1">{label}</p>
          )}
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-accent-blue/15 border border-accent-blue/30 flex items-center justify-center">
              <span className="text-xs font-bold text-accent-blue">
                {vendor.name.slice(0, 2).toUpperCase()}
              </span>
            </div>
            <div>
              <p className="text-base font-bold text-white leading-none">{vendor.name}</p>
              <p className="text-xs text-slate-500">{vendor.industry}</p>
            </div>
          </div>
        </div>
        <RiskBadge level={vendor.riskLevel} />
      </div>

      {/* Score */}
      <div className="flex items-baseline gap-3 mb-4">
        <span
          className="text-5xl font-black tabular leading-none"
          style={{ color: rc.stroke }}
        >
          {vendor.overallRiskScore}
        </span>
        <div>
          <p className="text-xs text-slate-500">Risk Score</p>
          <p className={`text-sm font-semibold ${DIRECTION_COLORS[vendor.riskDirection]}`}>
            {DIRECTION_ICONS[vendor.riskDirection]} {vendor.riskDirection}
          </p>
        </div>
      </div>

      {/* Key metrics */}
      <div className="grid grid-cols-2 gap-2 mb-4">
        <div className="bg-pg-surface rounded-lg border border-pg-border px-3 py-2">
          <p className="text-[10px] text-slate-500 uppercase tracking-wide mb-0.5">Dep. Exposure</p>
          <p className="text-lg font-bold tabular text-white">{vendor.dependencyExposure}%</p>
        </div>
        <div className="bg-pg-surface rounded-lg border border-pg-border px-3 py-2">
          <p className="text-[10px] text-slate-500 uppercase tracking-wide mb-0.5">HQ</p>
          <p className="text-sm font-semibold text-slate-300">{vendor.hq}</p>
        </div>
      </div>

      {/* Sparkline */}
      <div>
        <p className="text-[10px] text-slate-600 mb-1.5">12-Month Trend</p>
        <ResponsiveContainer width="100%" height={48}>
          <AreaChart data={vendor.riskTrend} margin={{ top: 0, right: 0, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id={`sparkGrad-${vendor.id}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%"   stopColor={rc.stroke} stopOpacity={0.3} />
                <stop offset="100%" stopColor={rc.stroke} stopOpacity={0}   />
              </linearGradient>
            </defs>
            <Area
              type="monotone"
              dataKey="score"
              stroke={rc.stroke}
              strokeWidth={1.5}
              fill={`url(#sparkGrad-${vendor.id})`}
              dot={false}
            />
            <Tooltip
              content={({ active, payload }) =>
                active && payload?.length
                  ? <div className="bg-pg-elevated border border-pg-border rounded-lg px-2 py-1 text-xs text-white shadow-xl">{payload[0].value}</div>
                  : null
              }
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </button>
  )
}
