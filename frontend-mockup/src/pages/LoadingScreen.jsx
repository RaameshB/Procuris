import { Shield, CheckCircle2 } from "lucide-react";
import { useState, useEffect } from "react";

const SCAN_CHECKS = [
  "Financial stability & credit risk",
  "Geopolitical exposure mapping",
  "Supply chain dependency analysis",
  "Regulatory compliance review",
  "Operational continuity assessment",
];

export default function LoadingScreen({ vendorName }) {
  const [visibleChecks, setVisibleChecks] = useState(0);

  useEffect(() => {
    if (visibleChecks >= SCAN_CHECKS.length) return;
    const id = setTimeout(() => setVisibleChecks((v) => v + 1), 520);
    return () => clearTimeout(id);
  }, [visibleChecks]);

  return (
    <div className="min-h-screen bg-pg-base flex items-center justify-center p-4 overflow-hidden">
      <style>{`
        @keyframes scanBar {
          0%   { transform: translateX(-150%); }
          100% { transform: translateX(450%); }
        }
        .anim-scan { animation: scanBar 1.8s linear infinite; }

        @keyframes orbitCw {
          from { transform: rotate(0deg); }
          to   { transform: rotate(360deg); }
        }
        @keyframes orbitCcw {
          from { transform: rotate(0deg); }
          to   { transform: rotate(-360deg); }
        }
        .spin-cw-2s  { animation: orbitCw  2s linear infinite; }
        .spin-cw-5s  { animation: orbitCw  5s linear infinite; }
        .spin-ccw-3s { animation: orbitCcw 3s linear infinite; }

        @keyframes checkIn {
          from { opacity: 0; transform: translateX(-6px); }
          to   { opacity: 1; transform: translateX(0); }
        }
        .anim-check-in {
          animation: checkIn 0.35s ease-out forwards;
        }
      `}</style>

      {/* Background grid */}
      <div
        className="fixed inset-0 opacity-[0.03] pointer-events-none"
        style={{
          backgroundImage:
            "linear-gradient(#3B82F6 1px, transparent 1px), linear-gradient(90deg, #3B82F6 1px, transparent 1px)",
          backgroundSize: "60px 60px",
        }}
      />

      {/* Corner frame decorations */}
      <div className="fixed top-6 left-6  w-10 h-10 border-l-2 border-t-2 border-accent-blue/25 rounded-tl-md" />
      <div className="fixed top-6 right-6 w-10 h-10 border-r-2 border-t-2 border-accent-blue/25 rounded-tr-md" />
      <div className="fixed bottom-6 left-6  w-10 h-10 border-l-2 border-b-2 border-accent-blue/25 rounded-bl-md" />
      <div className="fixed bottom-6 right-6 w-10 h-10 border-r-2 border-b-2 border-accent-blue/25 rounded-br-md" />

      {/* Subtle radial glow */}
      <div
        className="fixed inset-0 pointer-events-none"
        style={{
          background:
            "radial-gradient(ellipse 60% 50% at 50% 50%, rgba(59,130,246,0.06) 0%, transparent 70%)",
        }}
      />

      <div className="flex flex-col items-center gap-6 w-full max-w-xs animate-fade-in">
        {/* Mini brand */}
        <div className="flex items-center gap-2 opacity-70">
          <div className="w-6 h-6 rounded-md bg-accent-blue/15 border border-accent-blue/30 flex items-center justify-center">
            <Shield className="w-3 h-3 text-accent-blue" />
          </div>
          <span className="text-xs font-bold text-slate-400 tracking-wide uppercase">
            ProcureGuard
          </span>
        </div>

        {/* ── Animated Scanner ── */}
        <div className="relative w-36 h-36 flex items-center justify-center">
          {/* Outermost pulse halo */}
          <div className="absolute inset-0 rounded-full bg-accent-blue/5 animate-pulse" />

          {/* Outer dashed orbit ring */}
          <div
            className="spin-cw-5s absolute rounded-full"
            style={{
              inset: 0,
              border: "1px dashed rgba(59,130,246,0.25)",
            }}
          />

          {/* Spinning solid accent ring */}
          <div
            className="spin-cw-2s absolute rounded-full"
            style={{
              inset: 4,
              borderWidth: 2,
              borderStyle: "solid",
              borderColor: "transparent",
              borderTopColor: "#3B82F6",
              borderRightColor: "rgba(59,130,246,0.25)",
            }}
          />

          {/* Counter-spinning cyan ring */}
          <div
            className="spin-ccw-3s absolute rounded-full"
            style={{
              inset: 14,
              borderWidth: 1,
              borderStyle: "solid",
              borderColor: "transparent",
              borderBottomColor: "#06B6D4",
              borderLeftColor: "rgba(6,182,212,0.2)",
            }}
          />

          {/* Inner glow disc */}
          <div
            className="absolute rounded-full animate-pulse"
            style={{
              inset: 22,
              background:
                "radial-gradient(circle, rgba(59,130,246,0.2) 0%, transparent 70%)",
            }}
          />

          {/* Shield button centre */}
          <div
            className="relative z-10 w-14 h-14 rounded-full bg-pg-elevated border border-accent-blue/40 flex items-center justify-center"
            style={{
              boxShadow:
                "0 0 24px rgba(59,130,246,0.35), 0 0 8px rgba(59,130,246,0.15)",
            }}
          >
            <Shield className="w-7 h-7 text-accent-blue animate-pulse" />
          </div>
        </div>

        {/* Status label */}
        <div className="text-center space-y-1">
          <p className="text-base font-semibold text-white tracking-tight">
            Analyzing Risk Profile
          </p>
          {vendorName ? (
            <p className="text-sm text-accent-blue font-mono tracking-wide">
              {vendorName}
            </p>
          ) : (
            <p className="text-xs text-slate-600">Initializing engine…</p>
          )}
        </div>

        {/* Scan progress bar */}
        <div className="w-full h-0.5 bg-pg-border rounded-full overflow-hidden">
          <div className="anim-scan h-full w-1/3 bg-gradient-to-r from-transparent via-accent-blue to-transparent" />
        </div>

        {/* Scan check items */}
        <div className="w-full bg-pg-surface border border-pg-border rounded-2xl p-4 space-y-2.5 card-shadow">
          <p className="text-[10px] uppercase tracking-widest text-slate-600 mb-3">
            Running checks
          </p>
          {SCAN_CHECKS.map((check, i) => {
            const done = i < visibleChecks;
            return (
              <div
                key={check}
                className={`flex items-center gap-2.5 transition-opacity duration-300 ${
                  done ? "opacity-100" : "opacity-0"
                }`}
              >
                <CheckCircle2
                  className={`w-3.5 h-3.5 shrink-0 transition-colors duration-300 ${
                    done ? "text-risk-low" : "text-slate-700"
                  }`}
                />
                <span className="text-xs text-slate-400">{check}</span>
                {done && (
                  <span className="ml-auto text-[10px] font-mono text-risk-low/70">
                    ✓
                  </span>
                )}
              </div>
            );
          })}
        </div>

        {/* Pulsing dots + caption */}
        <div className="flex items-center gap-2">
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className="w-1.5 h-1.5 rounded-full bg-accent-blue/50 animate-pulse"
              style={{ animationDelay: `${i * 280}ms` }}
            />
          ))}
          <span className="text-xs text-slate-600 ml-1">
            Deep analysis in progress
          </span>
        </div>
      </div>
    </div>
  );
}
