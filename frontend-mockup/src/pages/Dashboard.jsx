import { useState } from 'react'
import Layout          from '../components/layout/Layout'
import VendorOverview  from '../components/tabs/VendorOverview'
import RiskBreakdown   from '../components/tabs/RiskBreakdown'
import RiskForecasting from '../components/tabs/RiskForecasting'
import VendorComparison from '../components/tabs/VendorComparison'
import { vendors }     from '../data/mockData'

const TAB_LABELS = {
  overview:    'Vendor Overview',
  breakdown:   'Multi-Layer Risk Breakdown',
  forecasting: 'Risk Forecasting',
  comparison:  'Vendor Comparison',
}

export default function Dashboard() {
  const [activeTab, setActiveTab]             = useState('overview')
  const [selectedVendorId, setSelectedVendorId] = useState('tsmc')

  const vendor = vendors[selectedVendorId] || vendors.tsmc

  const renderTab = () => {
    switch (activeTab) {
      case 'overview':    return <VendorOverview vendor={vendor} />
      case 'breakdown':   return <RiskBreakdown  vendor={vendor} />
      case 'forecasting': return <RiskForecasting vendor={vendor} />
      case 'comparison':  return <VendorComparison />
      default:            return <VendorOverview vendor={vendor} />
    }
  }

  return (
    <Layout
      activeTab={activeTab}
      onTabChange={setActiveTab}
      selectedVendorId={selectedVendorId}
      onVendorChange={setSelectedVendorId}
    >
      {/* Page header */}
      <div className="flex items-center justify-between mb-5">
        <div>
          <h1 className="text-xl font-bold text-white">{TAB_LABELS[activeTab]}</h1>
          {activeTab !== 'comparison' && (
            <p className="text-sm text-slate-500 mt-0.5">
              {vendor.name} · {vendor.industry} · {vendor.hq}
            </p>
          )}
        </div>

        {/* Risk score quick indicator */}
        {activeTab !== 'comparison' && (
          <div className="flex items-center gap-2 bg-pg-card border border-pg-border rounded-xl px-4 py-2">
            <div className="w-2 h-2 rounded-full bg-accent-blue animate-pulse" />
            <span className="text-xs text-slate-500">Risk Score</span>
            <span className="text-sm font-bold text-white tabular">{vendor.overallRiskScore}</span>
          </div>
        )}
      </div>

      {/* Tab content */}
      {renderTab()}
    </Layout>
  )
}
