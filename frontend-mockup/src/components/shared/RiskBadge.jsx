const LEVELS = {
  High:   { text: 'text-risk-high',  bg: 'bg-risk-high/10',  border: 'border-risk-high/25',  dot: 'bg-risk-high' },
  Medium: { text: 'text-risk-med',   bg: 'bg-risk-med/10',   border: 'border-risk-med/25',   dot: 'bg-risk-med'  },
  Low:    { text: 'text-risk-low',   bg: 'bg-risk-low/10',   border: 'border-risk-low/25',   dot: 'bg-risk-low'  },
}

export default function RiskBadge({ level, size = 'sm', showDot = true }) {
  const c = LEVELS[level] || LEVELS.Medium
  const sizeClass = size === 'lg'
    ? 'px-3 py-1.5 text-sm font-semibold'
    : 'px-2 py-0.5 text-xs font-medium'

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border ${c.bg} ${c.border} ${c.text} ${sizeClass}`}>
      {showDot && <span className={`w-1.5 h-1.5 rounded-full ${c.dot}`} />}
      {level}
    </span>
  )
}
