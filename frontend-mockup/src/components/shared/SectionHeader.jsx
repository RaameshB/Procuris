export default function SectionHeader({ label, title, className = '' }) {
  return (
    <div className={`mb-5 ${className}`}>
      {label && (
        <p className="text-xs uppercase tracking-widest text-slate-500 mb-1">{label}</p>
      )}
      <h2 className="text-lg font-semibold text-white">{title}</h2>
    </div>
  )
}
