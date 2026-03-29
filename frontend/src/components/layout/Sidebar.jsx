import {
  BarChart2,
  Layers,
  TrendingUp,
  GitCompare,
  Shield,
} from "lucide-react";

const TABS = [
  { id: "overview", label: "Vendor Overview", icon: BarChart2 },
  { id: "breakdown", label: "Risk Breakdown", icon: Layers },
  { id: "forecasting", label: "Risk Forecasting", icon: TrendingUp },
  { id: "comparison", label: "Vendor Comparison", icon: GitCompare },
];

export default function Sidebar({ activeTab, onTabChange }) {
  return (
    <aside className="w-56 shrink-0 bg-pg-surface border-r border-pg-border flex flex-col h-full">
      {/* Brand */}
      <div className="px-5 py-5 border-b border-pg-border flex items-center gap-2.5">
        <div className="w-8 h-8 rounded-lg bg-accent-blue/15 border border-accent-blue/30 flex items-center justify-center">
          <Shield className="w-4 h-4 text-accent-blue" />
        </div>
        <div>
          <p className="text-lg font-bold text-white leading-none">Procuris</p>
          <p className="text-sm text-slate-500 mt-0.5">Risk Intelligence</p>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 p-3 space-y-0.5">
        <p className="text-sm uppercase tracking-widest text-slate-600 px-3 py-2">
          Dashboard Menu
        </p>
        {TABS.map(({ id, label, icon: Icon }) => {
          const active = activeTab === id;
          return (
            <button
              key={id}
              onClick={() => onTabChange(id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 text-left
                ${
                  active
                    ? "bg-accent-blue/10 text-accent-blue border border-accent-blue/20"
                    : "text-slate-400 hover:bg-pg-muted hover:text-slate-200 border border-transparent"
                }`}
            >
              <Icon
                className={`w-4 h-4 shrink-0 ${active ? "text-accent-blue" : "text-slate-500"}`}
              />
              <span className="truncate">{label}</span>
              {active && (
                <span className="ml-auto w-1 h-1 rounded-full bg-accent-blue" />
              )}
            </button>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="p-3 border-t border-pg-border">
        <div className="flex items-center gap-2.5 px-2 py-2">
          <div className="w-7 h-7 rounded-full bg-gradient-to-br from-accent-blue to-accent-cyan flex items-center justify-center text-xs font-bold text-white shrink-0">
            U
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-slate-300 truncate">
              Demo User
            </p>
            <p className="text-xs text-slate-500 truncate">
              procurement@demo.io
            </p>
          </div>
        </div>
      </div>
    </aside>
  );
}
