import { useState, useEffect, useRef } from "react";
import Layout from "../components/layout/Layout";
import VendorOverview from "../components/tabs/VendorOverview";
import RiskBreakdown from "../components/tabs/RiskBreakdown";
import RiskForecasting from "../components/tabs/RiskForecasting";
import VendorComparison from "../components/tabs/VendorComparison";
import { apiFetch } from "../api";

const TAB_LABELS = {
  overview: "Vendor Overview",
  breakdown: "Multi-Layer Risk Breakdown",
  forecasting: "Risk Forecasting",
  comparison: "Vendor Comparison",
};

export default function Dashboard({
  initialVendorId = "tsmc",
  initialVendorData = null,
}) {
  const [activeTab, setActiveTab] = useState("overview");
  const [selectedVendorId, setSelectedVendorId] = useState(initialVendorId);
  const [vendor, setVendor] = useState(initialVendorData);
  const skipInitialFetch = useRef(!!initialVendorData);

  useEffect(() => {
    // Skip the first fetch if we were given pre-loaded data from VendorEntry
    if (skipInitialFetch.current) {
      skipInitialFetch.current = false;
      return;
    }

    async function loadData() {
      try {
        const result = await apiFetch(`/api/vendor/${selectedVendorId}`);
        setVendor(result.data);
      } catch (err) {
        console.error(err);
      }
    }

    loadData();
  }, [selectedVendorId]);

  const renderTab = () => {
    switch (activeTab) {
      case "overview":
        return <VendorOverview vendor={vendor} />;
      case "breakdown":
        return <RiskBreakdown vendor={vendor} />;
      case "forecasting":
        return <RiskForecasting vendor={vendor} />;
      case "comparison":
        return <VendorComparison />;
      default:
        return <VendorOverview vendor={vendor} />;
    }
  };

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
          <h1 className="text-xl font-bold text-white">
            {TAB_LABELS[activeTab]}
          </h1>
          {activeTab !== "comparison" && vendor && (
            <p className="text-sm text-slate-500 mt-0.5">
              {vendor.name} · {vendor.industry} · {vendor.hq}
            </p>
          )}
        </div>

        {/* Risk score quick indicator */}
        {activeTab !== "comparison" && vendor && (
          <div className="flex items-center gap-2 bg-pg-card border border-pg-border rounded-xl px-4 py-2">
            <div className="w-2 h-2 rounded-full bg-accent-blue animate-pulse" />
            <span className="text-xs text-slate-500">Risk Score</span>
            <span className="text-sm font-bold text-white tabular">
              {vendor.overallRiskScore}
            </span>
          </div>
        )}
      </div>

      {/* Loading state */}
      {!vendor && (
        <div className="flex items-center justify-center h-64">
          <div className="flex flex-col items-center gap-3">
            <div className="w-8 h-8 rounded-full border-2 border-transparent border-t-accent-blue animate-spin" />
            <p className="text-sm text-slate-500">Loading vendor data…</p>
          </div>
        </div>
      )}

      {/* Tab content */}
      {vendor && renderTab()}
    </Layout>
  );
}
