import { TrendingUp, Minus, TrendingDown } from 'lucide-react'

const DIRECTION_CONFIG = {
  Increasing: {
    icon: TrendingUp,
    label: 'Increasing',
    color: 'text-risk-high',
    bg: 'bg-risk-high/10',
    border: 'border-risk-high/30',
    glow: 'shadow-[0_0_24px_rgba(239,68,68,0.15)]',
    dot: 'bg-risk-high',
    description: 'Upstream risk is projected to escalate over the next forecasting window.',
  },
  Stable: {
    icon: Minus,
    label: 'Stable',
    color: 'text-risk-med',
    bg: 'bg-risk-med/10',
    border: 'border-risk-med/30',
    glow: 'shadow-[0_0_24px_rgba(245,158,11,0.12)]',
    dot: 'bg-risk-med',
    description: 'Upstream risk is expected to remain at current levels in the near term.',
  },
  Decreasing: {
    icon: TrendingDown,
    label: 'Decreasing',
    color: 'text-risk-low',
    bg: 'bg-risk-low/10',
    border: 'border-risk-low/30',
    glow: 'shadow-[0_0_24px_rgba(16,185,129,0.12)]',
    dot: 'bg-risk-low',
    description: 'Upstream risk signals suggest easing conditions ahead.',
  },
}

export default function RiskDirectionBadge({ direction }) {
  const cfg = DIRECTION_CONFIG[direction] || DIRECTION_CONFIG.Stable
  const Icon = cfg.icon

  return (
    <div className={`inline-flex items-center gap-4 px-6 py-4 rounded-2xl border ${cfg.bg} ${cfg.border} ${cfg.glow}`}>
      <div className={`w-10 h-10 rounded-xl ${cfg.bg} border ${cfg.border} flex items-center justify-center`}>
        <Icon className={`w-5 h-5 ${cfg.color}`} />
      </div>
      <div>
        <div className="flex items-center gap-2 mb-0.5">
          <span className={`w-1.5 h-1.5 rounded-full animate-pulse ${cfg.dot}`} />
          <p className="text-xs uppercase tracking-widest text-slate-500">Risk Direction</p>
        </div>
        <p className={`text-2xl font-bold ${cfg.color}`}>{cfg.label}</p>
        <p className="text-xs text-slate-500 mt-0.5 max-w-xs">{cfg.description}</p>
      </div>
    </div>
  )
}
