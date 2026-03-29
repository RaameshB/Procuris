import { useState } from 'react'
import { vendorList } from '../../../data/mockData'
import VendorCard       from './VendorCard'
import RadarComparison  from './RadarComparison'
import RecommendationCard from './RecommendationCard'

export default function VendorComparison() {
  const [vendorAId, setVendorAId] = useState('tsmc')
  const [vendorBId, setVendorBId] = useState('basf')

  const vendorA = vendorList.find(v => v.id === vendorAId) || vendorList[0]
  const vendorB = vendorList.find(v => v.id === vendorBId) || vendorList[1]

  // Ensure different vendors are selected
  const handleSelectA = (id) => { if (id !== vendorBId) setVendorAId(id) }
  const handleSelectB = (id) => { if (id !== vendorAId) setVendorBId(id) }

  return (
    <div className="space-y-5 animate-fade-in">
      {/* Vendor picker row */}
      <div className="bg-pg-surface rounded-2xl border border-pg-border p-5 card-shadow">
        <p className="text-xs uppercase tracking-widest text-slate-500 mb-4">Select Vendors to Compare</p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {vendorList.map(v => {
            const isA = v.id === vendorAId
            const isB = v.id === vendorBId
            return (
              <div key={v.id} className="space-y-1">
                <button
                  onClick={() => handleSelectA(v.id)}
                  className={`w-full px-3 py-2 rounded-lg border text-xs font-medium transition-all
                    ${isA ? 'bg-accent-blue/15 border-accent-blue/40 text-accent-blue' : 'bg-pg-card border-pg-border text-slate-400 hover:border-pg-muted hover:text-slate-300'}`}
                >
                  {v.name}
                  {isA && <span className="ml-1.5 text-[9px] opacity-70">A</span>}
                </button>
                <button
                  onClick={() => handleSelectB(v.id)}
                  className={`w-full px-3 py-2 rounded-lg border text-xs font-medium transition-all
                    ${isB ? 'bg-accent-cyan/15 border-accent-cyan/40 text-accent-cyan' : 'bg-pg-card border-pg-border text-slate-400 hover:border-pg-muted hover:text-slate-300'}`}
                >
                  {v.name}
                  {isB && <span className="ml-1.5 text-[9px] opacity-70">B</span>}
                </button>
              </div>
            )
          })}
        </div>
        <div className="flex gap-4 mt-3">
          <p className="text-[10px] text-slate-600">
            <span className="text-accent-blue font-semibold">Top row</span> = Vendor A &nbsp;·&nbsp;
            <span className="text-accent-cyan font-semibold">Bottom row</span> = Vendor B
          </p>
        </div>
      </div>

      {/* Head-to-head vendor cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <VendorCard vendor={vendorA} isSelected label="Vendor A" />
        <VendorCard vendor={vendorB} isSelected label="Vendor B" />
      </div>

      {/* Radar + Recommendation */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-5">
        <div className="lg:col-span-3 bg-pg-surface rounded-2xl border border-pg-border p-6 card-shadow">
          <RadarComparison vendorA={vendorA} vendorB={vendorB} />
        </div>
        <div className="lg:col-span-2">
          <RecommendationCard vendorA={vendorA} vendorB={vendorB} />
        </div>
      </div>
    </div>
  )
}
