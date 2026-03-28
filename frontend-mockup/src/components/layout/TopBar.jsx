import { useState } from 'react'
import { ChevronDown, Activity } from 'lucide-react'
import { vendorList } from '../../data/mockData'

const DIRECTION_STYLES = {
  Increasing: { color: 'text-risk-high',  bg: 'bg-risk-high/10',  border: 'border-risk-high/20'  },
  Stable:     { color: 'text-risk-med',   bg: 'bg-risk-med/10',   border: 'border-risk-med/20'   },
  Decreasing: { color: 'text-risk-low',   bg: 'bg-risk-low/10',   border: 'border-risk-low/20'   },
}

export default function TopBar({ selectedVendorId, onVendorChange, activeTab }) {
  const [open, setOpen] = useState(false)
  const selected = vendorList.find(v => v.id === selectedVendorId) || vendorList[0]
  const ds = DIRECTION_STYLES[selected.riskDirection] || DIRECTION_STYLES.Stable

  return (
    <header className="h-14 bg-pg-surface border-b border-pg-border flex items-center px-5 gap-4 shrink-0 relative z-30">
      {/* Vendor selector */}
      {activeTab !== 'comparison' ? (
        <div className="relative">
          <button
            onClick={() => setOpen(o => !o)}
            className="flex items-center gap-2.5 bg-pg-card border border-pg-border rounded-lg px-3 py-1.5 hover:border-pg-muted transition-colors"
          >
            <div className="w-6 h-6 rounded-md bg-accent-blue/15 flex items-center justify-center">
              <span className="text-[10px] font-bold text-accent-blue">
                {selected.name.slice(0, 2).toUpperCase()}
              </span>
            </div>
            <div className="text-left">
              <p className="text-sm font-semibold text-white leading-none">{selected.name}</p>
              <p className="text-[10px] text-slate-500">{selected.industry}</p>
            </div>
            <ChevronDown className={`w-3.5 h-3.5 text-slate-500 transition-transform ${open ? 'rotate-180' : ''}`} />
          </button>

          {open && (
            <div className="absolute top-full mt-1.5 left-0 w-56 bg-pg-elevated border border-pg-border rounded-xl shadow-2xl overflow-hidden animate-scale-in">
              {vendorList.map(v => (
                <button
                  key={v.id}
                  onClick={() => { onVendorChange(v.id); setOpen(false) }}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 hover:bg-pg-muted transition-colors text-left
                    ${v.id === selectedVendorId ? 'bg-accent-blue/10' : ''}`}
                >
                  <div className="w-6 h-6 rounded-md bg-pg-surface border border-pg-border flex items-center justify-center shrink-0">
                    <span className="text-[9px] font-bold text-slate-400">
                      {v.name.slice(0, 2).toUpperCase()}
                    </span>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-white leading-none">{v.name}</p>
                    <p className="text-[10px] text-slate-500">{v.industry} · {v.hq}</p>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      ) : (
        <div className="flex items-center gap-2">
          <div className="w-1.5 h-1.5 rounded-full bg-accent-cyan" />
          <span className="text-sm font-medium text-slate-300">Comparison Mode</span>
        </div>
      )}

      <div className="ml-auto flex items-center gap-3">
        {/* Live risk direction chip */}
        {activeTab !== 'comparison' && (
          <div className={`flex items-center gap-1.5 px-3 py-1 rounded-full border text-xs font-medium ${ds.color} ${ds.bg} ${ds.border}`}>
            <Activity className="w-3 h-3" />
            Risk {selected.riskDirection}
          </div>
        )}

        {/* Last updated */}
        <span className="text-xs text-slate-600">Updated Mar 28, 2026</span>

        {/* Avatar */}
        <div className="w-7 h-7 rounded-full bg-gradient-to-br from-accent-blue to-accent-cyan flex items-center justify-center text-xs font-bold text-white">
          U
        </div>
      </div>
    </header>
  )
}
