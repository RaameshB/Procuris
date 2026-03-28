import TierSplitDonut        from './TierSplitDonut'
import RiskDimensionBars     from './RiskDimensionBars'
import CrossLayerInsightsCard from './CrossLayerInsightsCard'

export default function RiskBreakdown({ vendor }) {
  return (
    <div className="space-y-5 animate-fade-in">
      {/* Row 1 — Donut + Dimension Bars side by side */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div className="bg-pg-surface rounded-2xl border border-pg-border p-6 card-shadow">
          <TierSplitDonut tierSplit={vendor.tierSplit} />
        </div>
        <div className="bg-pg-surface rounded-2xl border border-pg-border p-6 card-shadow">
          <RiskDimensionBars dimensions={vendor.riskDimensions} />
        </div>
      </div>

      {/* Row 2 — Cross-Layer Insights full width */}
      <div className="bg-pg-surface rounded-2xl border border-pg-border p-6 card-shadow">
        <CrossLayerInsightsCard insights={vendor.insights} />
      </div>
    </div>
  )
}
