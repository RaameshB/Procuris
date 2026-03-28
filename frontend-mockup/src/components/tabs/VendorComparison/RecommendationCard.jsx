import { CheckCircle2, Award } from 'lucide-react'

function getRecommendation(vendorA, vendorB) {
  const winner = vendorA.overallRiskScore <= vendorB.overallRiskScore ? vendorA : vendorB
  const loser  = winner.id === vendorA.id ? vendorB : vendorA

  const scoreDiff  = loser.overallRiskScore  - winner.overallRiskScore
  const exposeDiff = loser.dependencyExposure - winner.dependencyExposure

  const reasons = []

  reasons.push(
    `Lower overall risk score (${winner.overallRiskScore} vs ${loser.overallRiskScore}${scoreDiff > 0 ? ` — ${scoreDiff} pts safer` : ''}).`
  )

  if (exposeDiff > 0) {
    reasons.push(
      `Reduced dependency concentration: ${winner.dependencyExposure}% upstream exposure vs ${loser.dependencyExposure}% for ${loser.name}.`
    )
  } else {
    reasons.push(
      `Comparable upstream exposure with a more diversified supplier ecosystem.`
    )
  }

  const directionScore = { Decreasing: 0, Stable: 1, Increasing: 2 }
  if (directionScore[winner.riskDirection] <= directionScore[loser.riskDirection]) {
    reasons.push(
      `Risk trajectory is ${winner.riskDirection.toLowerCase()}, signalling a more favorable near-term outlook.`
    )
  } else {
    reasons.push(
      `Stronger geographic diversification reduces single-region concentration risk.`
    )
  }

  return { winner, loser, reasons: reasons.slice(0, 3) }
}

export default function RecommendationCard({ vendorA, vendorB }) {
  const { winner, loser, reasons } = getRecommendation(vendorA, vendorB)

  return (
    <div className="bg-gradient-to-br from-pg-card to-pg-elevated rounded-2xl border border-accent-blue/20 p-6 shadow-[0_0_32px_rgba(59,130,246,0.08)]">
      {/* Header */}
      <div className="flex items-center gap-2 mb-5">
        <Award className="w-4 h-4 text-accent-blue" />
        <p className="text-xs uppercase tracking-widest text-slate-500">Recommended Vendor</p>
      </div>

      {/* Winner banner */}
      <div className="flex items-center gap-4 mb-5 p-4 bg-accent-blue/8 rounded-xl border border-accent-blue/15">
        <div className="w-12 h-12 rounded-xl bg-accent-blue/15 border border-accent-blue/30 flex items-center justify-center shrink-0">
          <span className="text-lg font-black text-accent-blue">
            {winner.name.slice(0, 2).toUpperCase()}
          </span>
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-0.5">
            <span className="text-xl font-black text-white">{winner.name}</span>
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-accent-blue/15 border border-accent-blue/30 text-accent-blue text-[10px] font-bold uppercase tracking-wide">
              <CheckCircle2 className="w-2.5 h-2.5" /> Recommended
            </span>
          </div>
          <p className="text-sm text-slate-400">{winner.industry} · {winner.hq}</p>
        </div>
        <div className="text-right">
          <p className="text-3xl font-black text-white tabular">{winner.overallRiskScore}</p>
          <p className="text-[10px] text-slate-500">risk score</p>
        </div>
      </div>

      {/* VS divider */}
      <div className="flex items-center gap-3 mb-5">
        <div className="flex-1 h-px bg-pg-border" />
        <span className="text-xs text-slate-600 font-bold px-2">vs {loser.name} ({loser.overallRiskScore})</span>
        <div className="flex-1 h-px bg-pg-border" />
      </div>

      {/* Reasons */}
      <div className="space-y-3">
        {reasons.map((reason, i) => (
          <div key={i} className="flex items-start gap-3">
            <CheckCircle2 className="w-4 h-4 text-risk-low shrink-0 mt-0.5" />
            <p className="text-sm text-slate-300 leading-relaxed">{reason}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
