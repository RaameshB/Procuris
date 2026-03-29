import RiskDirectionBadge    from './RiskDirectionBadge'
import ForecastChart          from './ForecastChart'
import LeadingIndicatorsTable from './LeadingIndicatorsTable'

export default function RiskForecasting({ vendor }) {
  return (
    <div className="space-y-5 animate-fade-in">
      {/* Direction badge — prominent hero row */}
      <div className="bg-pg-surface rounded-2xl border border-pg-border p-6 card-shadow">
        <RiskDirectionBadge direction={vendor.riskDirection} />
      </div>

      {/* Forecast chart */}
      <div className="bg-pg-surface rounded-2xl border border-pg-border p-6 card-shadow">
        <ForecastChart data={vendor.forecast} />
      </div>

      {/* Leading indicators */}
      <div className="bg-pg-surface rounded-2xl border border-pg-border p-6 card-shadow">
        <LeadingIndicatorsTable indicators={vendor.leadingIndicators} />
      </div>
    </div>
  )
}
