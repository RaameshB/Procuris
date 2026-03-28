import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine,
} from 'recharts'

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-pg-elevated border border-pg-border rounded-xl px-3 py-2 shadow-xl">
      <p className="text-xs text-slate-500 mb-1">{label}</p>
      <p className="text-lg font-bold text-white tabular">{payload[0].value}</p>
      <p className="text-[10px] text-slate-500">Risk Score</p>
    </div>
  )
}

export default function RiskTrendLine({ data, vendorName }) {
  const scores = data.map(d => d.score)
  const minScore = Math.min(...scores) - 5
  const maxScore = Math.max(...scores) + 5
  const latest  = data[data.length - 1].score
  const first   = data[0].score
  const delta   = latest - first
  const rising  = delta > 0

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <div>
          <p className="text-xs uppercase tracking-widest text-slate-500 mb-1">Risk Trend (12 months)</p>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold text-white tabular">{latest}</span>
            <span className={`text-xs font-semibold px-1.5 py-0.5 rounded-md ${
              rising ? 'bg-risk-high/15 text-risk-high' : 'bg-risk-low/15 text-risk-low'
            }`}>
              {rising ? '+' : ''}{delta} pts
            </span>
          </div>
        </div>
        <span className="text-xs text-slate-500">vs 12 months ago</span>
      </div>

      <ResponsiveContainer width="100%" height={160}>
        <AreaChart data={data} margin={{ top: 8, right: 4, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id="trendGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%"   stopColor="#3B82F6" stopOpacity={0.3} />
              <stop offset="100%" stopColor="#3B82F6" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="#1C2A3E" strokeDasharray="3 3" vertical={false} />
          <XAxis
            dataKey="month"
            tick={{ fill: '#64748B', fontSize: 10 }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            domain={[minScore, maxScore]}
            tick={{ fill: '#64748B', fontSize: 10 }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ stroke: '#243550', strokeWidth: 1 }} />
          <ReferenceLine y={latest} stroke="#3B82F6" strokeDasharray="4 3" strokeOpacity={0.4} />
          <Area
            type="monotone"
            dataKey="score"
            stroke="#3B82F6"
            strokeWidth={2.5}
            fill="url(#trendGrad)"
            dot={false}
            activeDot={{ r: 5, fill: '#3B82F6', stroke: '#fff', strokeWidth: 2 }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
