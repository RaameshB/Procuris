import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  Tooltip, Legend, ResponsiveContainer,
} from 'recharts'

const AXES = [
  { key: 'geography',    label: 'Geography'     },
  { key: 'industry',     label: 'Industry'      },
  { key: 'logistics',    label: 'Logistics'     },
  { key: 'concentration',label: 'Concentration' },
  { key: 'volatility',   label: 'Volatility'    },
  { key: 'fragility',    label: 'Fragility'     },
]

function CustomTooltip({ active, payload }) {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-pg-elevated border border-pg-border rounded-xl px-3 py-2.5 shadow-xl">
      <p className="text-xs text-slate-500 mb-2">{payload[0]?.payload?.axis}</p>
      {payload.map(p => (
        <div key={p.dataKey} className="flex items-center gap-2 mb-1 last:mb-0">
          <span className="w-2 h-2 rounded-full" style={{ background: p.color }} />
          <span className="text-xs text-slate-400">{p.name}:</span>
          <span className="text-xs font-bold text-white tabular">{p.value}</span>
        </div>
      ))}
    </div>
  )
}

export default function RadarComparison({ vendorA, vendorB }) {
  const data = AXES.map(({ key, label }) => ({
    axis: label,
    [vendorA.name]: vendorA.radarDimensions[key] ?? 0,
    [vendorB.name]: vendorB.radarDimensions[key] ?? 0,
  }))

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <p className="text-xs uppercase tracking-widest text-slate-500">Risk Dimension Radar</p>
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5 text-xs text-slate-400">
            <span className="w-3 h-3 rounded-sm bg-accent-blue/30 border border-accent-blue/50 inline-block" />
            {vendorA.name}
          </span>
          <span className="flex items-center gap-1.5 text-xs text-slate-400">
            <span className="w-3 h-3 rounded-sm bg-accent-cyan/30 border border-accent-cyan/50 inline-block" />
            {vendorB.name}
          </span>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={320}>
        <RadarChart data={data} margin={{ top: 10, right: 30, bottom: 10, left: 30 }}>
          <PolarGrid
            gridType="polygon"
            stroke="#1C2A3E"
          />
          <PolarAngleAxis
            dataKey="axis"
            tick={{ fill: '#94A3B8', fontSize: 11, fontFamily: 'Inter, sans-serif' }}
          />
          <PolarRadiusAxis
            domain={[0, 100]}
            tick={false}
            axisLine={false}
            tickCount={5}
          />
          <Radar
            name={vendorA.name}
            dataKey={vendorA.name}
            stroke="#3B82F6"
            fill="#3B82F6"
            fillOpacity={0.15}
            strokeWidth={2}
            dot={{ fill: '#3B82F6', r: 3, stroke: 'none' }}
          />
          <Radar
            name={vendorB.name}
            dataKey={vendorB.name}
            stroke="#06B6D4"
            fill="#06B6D4"
            fillOpacity={0.12}
            strokeWidth={2}
            dot={{ fill: '#06B6D4', r: 3, stroke: 'none' }}
          />
          <Tooltip content={<CustomTooltip />} />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  )
}
