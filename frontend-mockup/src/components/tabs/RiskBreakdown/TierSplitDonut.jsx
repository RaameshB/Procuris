import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts'

const COLORS = { tier2: '#3B82F6', tier3: '#06B6D4' }

function CustomTooltip({ active, payload }) {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-pg-elevated border border-pg-border rounded-xl px-3 py-2 shadow-xl">
      <p className="text-xs font-semibold text-white">{payload[0].name}</p>
      <p className="text-lg font-bold tabular" style={{ color: payload[0].payload.color }}>
        {payload[0].value}%
      </p>
    </div>
  )
}

export default function TierSplitDonut({ tierSplit }) {
  const data = [
    { name: 'Tier-2', value: tierSplit.tier2, color: COLORS.tier2 },
    { name: 'Tier-3', value: tierSplit.tier3, color: COLORS.tier3 },
  ]
  const dominant  = tierSplit.tier3 >= tierSplit.tier2 ? 'Tier-3' : 'Tier-2'
  const pct       = tierSplit.tier3 >= tierSplit.tier2 ? tierSplit.tier3 : tierSplit.tier2
  const centerColor = tierSplit.tier3 >= tierSplit.tier2 ? COLORS.tier3 : COLORS.tier2

  return (
    <div>
      <p className="text-xs uppercase tracking-widest text-slate-500 mb-4">Tier-2 vs Tier-3 Risk Split</p>

      <div className="relative">
        <ResponsiveContainer width="100%" height={220}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={65}
              outerRadius={90}
              paddingAngle={3}
              dataKey="value"
              strokeWidth={0}
              label={false}
            >
              {data.map((entry) => (
                <Cell key={entry.name} fill={entry.color} opacity={0.85} />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
          </PieChart>
        </ResponsiveContainer>

        {/* Center label overlay */}
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
          <span className="text-3xl font-black tabular leading-none" style={{ color: centerColor }}>
            {pct}%
          </span>
          <span className="text-xs text-slate-500 mt-1">{dominant} dominant</span>
        </div>
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center gap-6 mt-2">
        {data.map(d => (
          <div key={d.name} className="flex items-center gap-2">
            <div className="w-8 h-2 rounded-full" style={{ background: d.color, opacity: 0.8 }} />
            <div>
              <p className="text-xs font-semibold text-slate-300">{d.name}</p>
              <p className="text-lg font-bold tabular" style={{ color: d.color }}>{d.value}%</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
