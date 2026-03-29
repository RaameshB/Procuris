export default function MetricCard({ label, value, sub, accent = false, className = '' }) {
  return (
    <div className={`bg-pg-card rounded-xl border border-pg-border p-4 ${className}`}>
      <p className="text-xs uppercase tracking-widest text-slate-500 mb-2">{label}</p>
      <p className={`text-3xl font-bold tabular leading-none ${accent ? 'text-accent-blue' : 'text-white'}`}>
        {value}
      </p>
      {sub && <p className="text-xs text-slate-500 mt-2">{sub}</p>}
    </div>
  )
}
