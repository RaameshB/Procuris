const RISK_STYLES = {
  High:   { badge: 'bg-risk-high/10 text-risk-high border-risk-high/25',  bar: 'bg-risk-high'  },
  Medium: { badge: 'bg-risk-med/10  text-risk-med  border-risk-med/25',   bar: 'bg-risk-med'   },
  Low:    { badge: 'bg-risk-low/10  text-risk-low  border-risk-low/25',   bar: 'bg-risk-low'   },
}

const TIER_STYLES = {
  T2: 'bg-accent-blue/10 text-accent-blue border-accent-blue/25',
  T3: 'bg-accent-cyan/10 text-accent-cyan border-accent-cyan/25',
}

function ExposureRow({ item, index }) {
  const rs = RISK_STYLES[item.riskLevel] || RISK_STYLES.Medium
  const ts = TIER_STYLES[item.tier] || TIER_STYLES.T2

  return (
    <div
      className="flex items-center gap-4 py-3 border-b border-pg-border last:border-0 animate-slide-up"
      style={{ animationDelay: `${index * 60}ms`, animationFillMode: 'both' }}
    >
      {/* Rank */}
      <span className="text-xs font-bold text-slate-600 tabular w-4 text-center">{index + 1}</span>

      {/* Industry info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1.5">
          <span className="text-sm font-medium text-slate-200 truncate">{item.industry}</span>
          <span className={`inline-flex px-1.5 py-0.5 text-[9px] font-bold rounded border ${ts} shrink-0`}>
            {item.tier}
          </span>
        </div>
        {/* Exposure bar */}
        <div className="flex items-center gap-2">
          <div className="flex-1 h-1.5 bg-pg-border rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-700 ease-out ${rs.bar}`}
              style={{ width: `${item.exposure}%`, opacity: 0.75 }}
            />
          </div>
          <span className="text-xs font-semibold text-slate-300 tabular w-8 text-right">{item.exposure}%</span>
        </div>
      </div>

      {/* Risk badge */}
      <span className={`inline-flex items-center px-2 py-0.5 rounded-full border text-[10px] font-semibold shrink-0 ${rs.badge}`}>
        {item.riskLevel}
      </span>
    </div>
  )
}

export default function IndustryExposureGrid({ data }) {
  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <p className="text-xs uppercase tracking-widest text-slate-500">Upstream Industry Exposure</p>
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1 text-[10px] text-accent-blue">
            <span className="w-2 h-2 rounded-sm bg-accent-blue/30 border border-accent-blue/40" /> Tier-2
          </span>
          <span className="inline-flex items-center gap-1 text-[10px] text-accent-cyan">
            <span className="w-2 h-2 rounded-sm bg-accent-cyan/30 border border-accent-cyan/40" /> Tier-3
          </span>
        </div>
      </div>
      <div>
        {data.map((item, i) => (
          <ExposureRow key={item.industry} item={item} index={i} />
        ))}
      </div>
    </div>
  )
}
