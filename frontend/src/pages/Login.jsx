import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Shield, ArrowRight, Lock } from "lucide-react";
import { supabase } from "../lib/supabase";

export default function Login() {
  const navigate = useNavigate();

  useEffect(() => {
    document.title = "Login – Procuris";
  }, []);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const { error: err } = await supabase.auth.signInWithPassword({
        email,
        password,
      });
      if (err) throw err;
      navigate("/dashboard");
    } catch (err) {
      setError(err.message || "Login failed. Try demo mode.");
    } finally {
      setLoading(false);
    }
  };

  const handleDemo = () => navigate("/dashboard");

  return (
    <div className="min-h-screen bg-pg-base flex items-center justify-center p-4">
      {/* Background grid */}
      <div
        className="fixed inset-0 opacity-[0.03] pointer-events-none"
        style={{
          backgroundImage:
            "linear-gradient(#3B82F6 1px, transparent 1px), linear-gradient(90deg, #3B82F6 1px, transparent 1px)",
          backgroundSize: "60px 60px",
        }}
      />

      <div className="w-full max-w-sm animate-slide-up">
        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-accent-blue/10 border border-accent-blue/25 flex items-center justify-center mb-4 shadow-[0_0_32px_rgba(59,130,246,0.15)]">
            <Shield className="w-7 h-7 text-accent-blue" />
          </div>
          <h1 className="text-2xl font-bold text-white">Procuris</h1>
          <p className="text-sm text-slate-500 mt-1">
            Procurement Risk Intelligence
          </p>
        </div>

        {/* Card */}
        <div className="bg-pg-surface rounded-2xl border border-pg-border p-6 card-shadow">
          <p className="text-sm font-semibold text-white mb-5">
            Sign in to your account
          </p>

          <form onSubmit={handleLogin} className="space-y-3">
            <div>
              <label className="text-xs text-slate-500 mb-1.5 block uppercase tracking-wide">
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@company.com"
                className="w-full bg-pg-card border border-pg-border rounded-lg px-3 py-2.5 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-accent-blue/50 focus:ring-1 focus:ring-accent-blue/20 transition-colors"
              />
            </div>
            <div>
              <label className="text-xs text-slate-500 mb-1.5 block uppercase tracking-wide">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-pg-card border border-pg-border rounded-lg px-3 py-2.5 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-accent-blue/50 focus:ring-1 focus:ring-accent-blue/20 transition-colors"
              />
            </div>

            {error && (
              <p className="text-xs text-risk-high bg-risk-high/10 border border-risk-high/20 rounded-lg px-3 py-2">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 bg-accent-blue hover:bg-blue-400 text-white font-semibold py-2.5 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm mt-1"
            >
              <Lock className="w-3.5 h-3.5" />
              {loading ? "Signing in..." : "Sign In"}
            </button>
          </form>

          <div className="relative my-4">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full h-px bg-pg-border" />
            </div>
            <div className="relative flex justify-center">
              <span className="bg-pg-surface px-2 text-xs text-slate-600">
                or
              </span>
            </div>
          </div>

          <button
            onClick={handleDemo}
            className="w-full flex items-center justify-center gap-2 bg-pg-card hover:bg-pg-elevated border border-pg-border hover:border-pg-muted text-slate-300 font-medium py-2.5 rounded-lg transition-all text-sm"
          >
            View Demo Dashboard
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <p className="text-center text-xs text-slate-600 mt-5">
          Powered by Procuris Intelligence Engine · v1.0
        </p>
      </div>
    </div>
  );
}
