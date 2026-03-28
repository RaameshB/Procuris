import { Sparkles } from 'lucide-react'

const SEVERITY_STYLES = {
  high: { border: 'border-l-risk-high', badge: 'bg-risk-high/10 text-risk-high border-risk-high/25' },
  med:  { border: 'border-l-risk-med',  badge: 'bg-risk-med/10  text-risk-med  border-risk-med/25'  },
  low:  { border: 'border-l-risk-low',  badge: 'bg-risk-low/10  text-risk-low  border-risk-low/25'  },
}

const LAYER_STYLES = {
  'Tier-2': 'bg-accent-blue/10 text-accent-blue border-accent-blue/25',
  'Tier-3': 'bg-accent-cyan/10 text-accent-cyan border-accent-cyan/25',
}

export default function CrossLayerInsightsCard({ insights }) {
  return (
    <div>
      <div className="flex items-center gap-2 mb-4">
        <Sparkles className="w-3.5 h-3.5 text-accent-purple" />
        <p className="text-xs uppercase tracking-widest text-slate-500">Cross-Layer Insights</p>
      </div>

      <div className="space-y-3">
        {insights.map((insight, i) => {
          const sv = SEVERITY_STYLES[insight.severity] || SEVERITY_STYLES.med
          const lv = LAYER_STYLES[insight.layer] || LAYER_STYLES['Tier-2']
          return (
            <div
              key={insight.id}
              className={`bg-pg-card rounded-xl border-l-2 border border-pg-border pl-4 pr-4 py-3.5 animate-slide-up ${sv.border}`}
              style={{ animationDelay: `${i * 80}ms`, animationFillMode: 'both' }}
            >
              <div className="flex items-center gap-2 mb-2">
                <span className={`inline-flex px-2 py-0.5 rounded-full border text-[10px] font-semibold ${lv}`}>
                  {insight.layer}
                </span>
                <span className="text-slate-600">·</span>
                <span className={`inline-flex px-2 py-0.5 rounded-full border text-[10px] font-medium ${sv.badge}`}>
                  {insight.dimension}
                </span>
              </div>
              <p className="text-sm text-slate-300 leading-relaxed">{insight.text}</p>
            </div>
          )
        })}
      </div>
    </div>
  )
}
