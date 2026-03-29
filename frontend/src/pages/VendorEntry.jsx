import { useState } from "react";
import { Shield, Search, AlertCircle } from "lucide-react";

export default function VendorEntry({ onSearch, error }) {
  const [vendorName, setVendorName] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    const trimmed = vendorName.trim().toLowerCase();
    if (!trimmed) return;
    onSearch(trimmed);
  };

  return (
    <div className="min-h-screen bg-pg-base flex items-center justify-center p-4">
      {/* Background grid */}
      <div
        className="fixed inset-0 opacity-[0.15] pointer-events-none"
        style={{
          backgroundImage:
            "linear-gradient(#2E2E9E 4px, transparent 1px), linear-gradient(90deg, #2E2E9E 4px, transparent 1px)",
          backgroundSize: "60px 60px",
        }}
      />

      {/* Corner frame decorations */}
      <div className="fixed top-6 left-6  w-10 h-10 border-l-4 border-t-4 border-white/40 rounded-tl-md" />
      <div className="fixed top-6 right-6 w-10 h-10 border-r-4 border-t-4 border-white/40 rounded-tr-md" />
      <div className="fixed bottom-6 left-6  w-10 h-10 border-l-4 border-b-4 border-white/40 rounded-bl-md" />
      <div className="fixed bottom-6 right-6 w-10 h-10 border-r-4 border-b-4 border-white/40 rounded-br-md" />

      <div className="relative w-full max-w-sm animate-slide-up">
        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-20 h-20 p-2 rounded-2xl bg-accent-blue/10 border border-accent-blue/25 flex items-center justify-center mb-4 shadow-[0_0_32px_rgba(59,130,246,0.15)]">
            <Shield className="w-20 h-20 text-accent-blue" />
          </div>
          <h1 className="text-6xl font-bold text-white">ProcureGuard</h1>
          <p className="text-xl text-slate-500 mt-1">
            Procurement Risk Intelligence
          </p>
        </div>

        {/* Card */}
        <div className="bg-pg-surface rounded-2xl border border-pg-border p-6 card-shadow">
          <p className="text-xl font-semibold text-white mb-1">
            Analyze a vendor
          </p>
          <p className="text-sm text-slate-500 mb-5">
            Enter a vendor name to begin a comprehensive risk assessment.
          </p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-sm text-slate-500 mb-1.5 block uppercase tracking-wide">
                Vendor Name
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={vendorName}
                  onChange={(e) => setVendorName(e.target.value)}
                  placeholder="e.g. TSMC, Apple, Samsung…"
                  autoFocus
                  className="flex-1 bg-pg-card border border-pg-border rounded-lg px-3 py-2.5 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-accent-blue/50 focus:ring-1 focus:ring-accent-blue/20 transition-colors"
                />
                <button
                  type="submit"
                  disabled={!vendorName.trim()}
                  className="flex items-center mr-3 gap-1 bg-accent-blue hover:bg-blue-400 text-white font-semibold px-4 py-2.5 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm whitespace-nowrap"
                >
                  <Search className="w-3.5 h-3.5" />
                  Analyze
                </button>
              </div>
            </div>
          </form>

          {error && (
            <div className="flex items-start gap-2 mt-4 text-xs text-risk-high bg-risk-high/10 border border-risk-high/20 rounded-lg px-3 py-2.5 animate-fade-in">
              <AlertCircle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}
        </div>

        <p className="text-center text-xs text-slate-600 mt-5">
          Powered by ProcureGuard Intelligence Engine · v1.0
        </p>
      </div>
    </div>
  );
}
