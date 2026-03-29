import { Activity } from "lucide-react";

export default function TopBar({ activeTab, vendor }) {
  return (
    <header className="bg-pg-surface border-b border-pg-border flex items-center px-6 py-3 gap-4 shrink-0 relative z-30">
      {/* Left: vendor identity or comparison mode label */}
      {activeTab !== "comparison" && vendor ? (
        <div>
          <p className="text-4xl font-bold text-white leading-tight">
            {vendor.name}
          </p>
          <p className="text-sm text-slate-400 mt-0.5">
            {vendor.industry} · {vendor.hq}
          </p>
        </div>
      ) : activeTab === "comparison" ? (
        <div className="flex items-center gap-2">
          <div className="w-1.5 h-1.5 rounded-full bg-accent-cyan" />
          <span className="text-sm font-medium text-slate-300">
            Comparison Mode
          </span>
        </div>
      ) : null}

      {/* Right side */}
      <div className="ml-auto flex items-center gap-3">
        {/* Live risk direction chip */}
        {activeTab !== "comparison" && vendor?.riskDirection && (
          <div
            className={`flex items-center gap-1.5 px-3 py-1 rounded-full border text-md font-medium
              ${vendor.riskDirection === "Increasing" ? "text-risk-high bg-risk-high/10 border-risk-high/20" : ""}
              ${vendor.riskDirection === "Stable" ? "text-risk-med  bg-risk-med/10  border-risk-med/20" : ""}
              ${vendor.riskDirection === "Decreasing" ? "text-risk-low  bg-risk-low/10  border-risk-low/20" : ""}
            `}
          >
            <Activity className="w-3 h-3" />
            Risk {vendor.riskDirection}
          </div>
        )}

        {/* Last updated */}
        <span className="text-md text-slate-600">Updated Mar 28, 2026</span>

        {/* Avatar */}
        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-accent-blue to-accent-cyan flex items-center justify-center text-xl font-bold text-white">
          U
        </div>
      </div>
    </header>
  );
}
