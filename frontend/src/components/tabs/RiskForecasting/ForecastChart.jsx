import {
  ComposedChart, Area, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine,
} from 'recharts'

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  const actual   = payload.find(p => p.dataKey === 'actual')
  const forecast = payload.find(p => p.dataKey === 'forecast')
  const upper    = payload.find(p => p.dataKey === 'upper')
  const lower    = payload.find(p => p.dataKey === 'lower')
  const val = actual?.value ?? forecast?.value

  return (
    <div className="bg-pg-elevated border border-pg-border rounded-xl px-3 py-2.5 shadow-xl">
      <p className="text-xs text-slate-500 mb-2">{label}</p>
      {val != null && (
        <div className="flex items-center gap-2 mb-1">
          <span className={`text-xs font-medium ${actual ? 'text-accent-blue' : 'text-accent-cyan'}`}>
            {actual ? 'Actual' : 'Forecast'}
          </span>
          <span className="text-sm font-bold text-white tabular">{val}</span>
        </div>
      )}
      {upper?.value != null && lower?.value != null && (
        <p className="text-[10px] text-slate-500">Range: {lower.value} – {upper.value}</p>
      )}
    </div>
  )
}

export default function ForecastChart({ data }) {
  // Build chart data with band = upper - lower for stacking
  const chartData = data.map(d => ({
    ...d,
    band: d.upper != null && d.lower != null ? d.upper - d.lower : null,
  }))

  // Find the transition period (last actual → first forecast)
  const transitionPeriod = data.find(d => d.actual == null && d.forecast != null)?.period

  const allValues = data.flatMap(d =>
    [d.actual, d.forecast, d.upper, d.lower].filter(v => v != null)
  )
  const minY = Math.min(...allValues) - 6
  const maxY = Math.max(...allValues) + 6

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <p className="text-xs uppercase tracking-widest text-slate-500">Forecasted Risk Trend</p>
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5 text-[10px] text-slate-400">
            <span className="w-5 h-0.5 bg-accent-blue rounded-full inline-block" /> Historical
          </span>
          <span className="flex items-center gap-1.5 text-[10px] text-slate-400">
            <span className="w-5 h-0 border-t-2 border-dashed border-accent-cyan inline-block" /> Forecast
          </span>
          <span className="flex items-center gap-1.5 text-[10px] text-slate-400">
            <span className="w-3 h-3 rounded bg-accent-blue/15 inline-block" /> Confidence band
          </span>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={240}>
        <ComposedChart data={chartData} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id="actualGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%"   stopColor="#3B82F6" stopOpacity={0.15} />
              <stop offset="100%" stopColor="#3B82F6" stopOpacity={0}    />
            </linearGradient>
          </defs>

          <CartesianGrid stroke="#1C2A3E" strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="period" tick={{ fill: '#64748B', fontSize: 10 }} axisLine={false} tickLine={false} />
          <YAxis domain={[minY, maxY]} tick={{ fill: '#64748B', fontSize: 10 }} axisLine={false} tickLine={false} />
          <Tooltip content={<CustomTooltip />} cursor={{ stroke: '#243550', strokeWidth: 1 }} />

          {/* Confidence band: transparent base + colored band stacked */}
          <Area
            type="monotone"
            dataKey="lower"
            stackId="ci"
            stroke="none"
            fill="transparent"
            legendType="none"
            connectNulls={false}
          />
          <Area
            type="monotone"
            dataKey="band"
            stackId="ci"
            stroke="none"
            fill="#06B6D4"
            fillOpacity={0.1}
            legendType="none"
            connectNulls={false}
          />

          {/* Actual historical area */}
          <Area
            type="monotone"
            dataKey="actual"
            stroke="#3B82F6"
            strokeWidth={2.5}
            fill="url(#actualGrad)"
            dot={false}
            activeDot={{ r: 5, fill: '#3B82F6', stroke: '#fff', strokeWidth: 2 }}
            connectNulls={false}
          />

          {/* Forecast dashed line */}
          <Line
            type="monotone"
            dataKey="forecast"
            stroke="#06B6D4"
            strokeWidth={2}
            strokeDasharray="6 3"
            dot={{ fill: '#06B6D4', r: 3, stroke: 'none' }}
            activeDot={{ r: 5, fill: '#06B6D4', stroke: '#fff', strokeWidth: 2 }}
            connectNulls={false}
          />

          {/* Vertical divider at forecast start */}
          {transitionPeriod && (
            <ReferenceLine
              x={transitionPeriod}
              stroke="#243550"
              strokeDasharray="4 3"
              label={{ value: 'Forecast →', fill: '#64748B', fontSize: 9, position: 'insideTopLeft' }}
            />
          )}
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}
