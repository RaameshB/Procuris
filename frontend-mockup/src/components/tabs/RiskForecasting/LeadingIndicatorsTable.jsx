import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

const SEVERITY_STYLES = {
  high: { badge: 'bg-risk-high/10 text-risk-high border-risk-high/25', dot: 'bg-risk-high' },
  med:  { badge: 'bg-risk-med/10  text-risk-med  border-risk-med/25',  dot: 'bg-risk-med'  },
  low:  { badge: 'bg-risk-low/10  text-risk-low  border-risk-low/25',  dot: 'bg-risk-low'  },
}

const TREND_CONFIG = {
  up:     { icon: TrendingUp,   color: 'text-risk-high'  },
  down:   { icon: TrendingDown, color: 'text-risk-low'   },
  stable: { icon: Minus,        color: 'text-slate-400'  },
}

export default function LeadingIndicatorsTable({ indicators }) {
  return (
    <div>
      <p className="text-xs uppercase tracking-widest text-slate-500 mb-4">Leading Indicators</p>

      <div className="space-y-1">
        {/* Header row */}
        <div className="grid grid-cols-12 gap-2 px-3 pb-2 border-b border-pg-border">
          <span className="col-span-5 text-[10px] uppercase tracking-wider text-slate-600">Signal</span>
          <span className="col-span-3 text-[10px] uppercase tracking-wider text-slate-600">Value</span>
          <span className="col-span-2 text-[10px] uppercase tracking-wider text-slate-600">Trend</span>
          <span className="col-span-2 text-[10px] uppercase tracking-wider text-slate-600">Severity</span>
        </div>

        {indicators.map((ind, i) => {
          const sv = SEVERITY_STYLES[ind.severity] || SEVERITY_STYLES.low
          const tr = TREND_CONFIG[ind.trend]    || TREND_CONFIG.stable
          const TrendIcon = tr.icon

          return (
            <div
              key={ind.signal}
              className="grid grid-cols-12 gap-2 items-center px-3 py-2.5 rounded-lg hover:bg-pg-card transition-colors animate-slide-up"
              style={{ animationDelay: `${i * 50}ms`, animationFillMode: 'both' }}
            >
              {/* Signal name */}
              <div className="col-span-5 flex items-center gap-2">
                <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${sv.dot}`} />
                <span className="text-sm text-slate-300 leading-tight">{ind.signal}</span>
              </div>

              {/* Value */}
              <span className="col-span-3 text-sm font-semibold text-white tabular">{ind.value}</span>

              {/* Trend */}
              <div className="col-span-2 flex items-center gap-1">
                <TrendIcon className={`w-3.5 h-3.5 ${tr.color}`} />
                <span className={`text-xs capitalize ${tr.color}`}>{ind.trend}</span>
              </div>

              {/* Severity */}
              <div className="col-span-2">
                <span className={`inline-flex items-center px-2 py-0.5 rounded-full border text-[10px] font-semibold capitalize ${sv.badge}`}>
                  {ind.severity === 'med' ? 'Medium' : ind.severity.charAt(0).toUpperCase() + ind.severity.slice(1)}
                </span>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
