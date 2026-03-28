import RiskScoreGauge      from './RiskScoreGauge'
import DependencyExposureBar from './DependencyExposureBar'
import RiskTrendLine         from './RiskTrendLine'
import IndustryExposureGrid  from './IndustryExposureGrid'

export default function VendorOverview({ vendor }) {
  return (
    <div className="space-y-5 animate-fade-in">
      {/* Row 1 — Hero: gauge + dependency */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Gauge — spans 1 col, visually dominant */}
        <div className="bg-pg-surface rounded-2xl border border-pg-border p-6 card-shadow flex flex-col items-center justify-center gap-3">
          <p className="text-xs uppercase tracking-widest text-slate-500 self-start w-full">Overall Risk Score</p>
          <RiskScoreGauge score={vendor.overallRiskScore} riskLevel={vendor.riskLevel} />
          <div className="grid grid-cols-2 gap-3 w-full mt-1">
            <div className="bg-pg-card rounded-lg border border-pg-border px-3 py-2 text-center">
              <p className="text-[10px] text-slate-500 uppercase tracking-wide">Industry</p>
              <p className="text-xs font-semibold text-slate-300 mt-0.5">{vendor.industry}</p>
            </div>
            <div className="bg-pg-card rounded-lg border border-pg-border px-3 py-2 text-center">
              <p className="text-[10px] text-slate-500 uppercase tracking-wide">HQ</p>
              <p className="text-xs font-semibold text-slate-300 mt-0.5">{vendor.hq}</p>
            </div>
          </div>
        </div>

        {/* Dependency Exposure — spans 1 col */}
        <div className="bg-pg-surface rounded-2xl border border-pg-border p-6 card-shadow">
          <DependencyExposureBar exposure={vendor.dependencyExposure} />
        </div>

        {/* Risk Trend Line — spans 1 col */}
        <div className="bg-pg-surface rounded-2xl border border-pg-border p-6 card-shadow">
          <RiskTrendLine data={vendor.riskTrend} vendorName={vendor.name} />
        </div>
      </div>

      {/* Row 2 — Industry Exposure */}
      <div className="bg-pg-surface rounded-2xl border border-pg-border p-6 card-shadow">
        <IndustryExposureGrid data={vendor.industryExposure} />
      </div>
    </div>
  )
}
