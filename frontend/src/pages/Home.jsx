import { useState, useCallback, useEffect, useRef } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import VendorEntry from "./VendorEntry";
import LoadingScreen from "./LoadingScreen";
import Dashboard from "./Dashboard";
import { apiFetch } from "../api";

const FADE_DURATION = 350; // ms – matches CSS transition
const MIN_LOADING_MS = 1600; // minimum time to show the loading screen

export default function Home() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const vendorParam = searchParams.get("vendor");

  // On a cold load to /dashboard?vendor=..., start in "loading" phase right
  // away so the VendorEntry screen never flashes before the fetch begins.
  const [phase, setPhase] = useState(() =>
    new URLSearchParams(window.location.search).get("vendor")
      ? "loading"
      : "entry",
  );
  const [visible, setVisible] = useState(true);
  const [vendorData, setVendorData] = useState(null);
  const [vendorId, setVendorId] = useState(null);
  const [entryError, setEntryError] = useState(null);

  // Tracks whether the vendorParam effect is running for the very first time.
  // Used to distinguish a cold page load (no fade needed) from a navigate() call.
  const isFirstEffect = useRef(true);

  // Carries an error message from an async catch block over to the
  // !vendorParam effect branch, which owns the fade-back-to-entry transition.
  const pendingErrorRef = useRef(null);

  /**
   * Fade the current screen out, swap to nextPhase, then fade back in.
   * `setup` runs just before the phase swap so new state is ready the moment
   * the incoming component first renders.
   */
  const fadeTo = useCallback((nextPhase, setup) => {
    setVisible(false);
    setTimeout(() => {
      setup?.();
      setPhase(nextPhase);
      // One rAF so the new component is painted at opacity-0 before we
      // start the fade-in transition.
      requestAnimationFrame(() => setVisible(true));
    }, FADE_DURATION);
  }, []);

  useEffect(() => {
    const isFirst = isFirstEffect.current;
    isFirstEffect.current = false;

    // ── URL cleared: back button, error redirect, or direct nav to "/" ────────
    if (!vendorParam) {
      if (isFirst) {
        // Initial load on "/" — already showing VendorEntry, nothing to do.
        return;
      }
      // Animate back to entry, picking up any error stored by a failed fetch.
      const error = pendingErrorRef.current;
      pendingErrorRef.current = null;
      // Defer out of the synchronous effect body to avoid cascading-render warning.
      requestAnimationFrame(() => fadeTo("entry", () => setEntryError(error)));
      return;
    }

    // ── A vendor param is present — run the fetch ─────────────────────────────
    let cancelled = false;

    const runFetch = async () => {
      setEntryError(null);

      // Cold load: component already starts in "loading" phase, no fade needed.
      // Navigate from VendorEntry: we're in "entry" phase, so fade to loading.
      if (!isFirst) {
        fadeTo("loading");
      }

      const start = Date.now();

      try {
        const result = await apiFetch(
          `/api/vendors/?vendor_name=${vendorParam}`,
        );
        if (cancelled) return;

        // Keep the loading screen up for at least MIN_LOADING_MS.
        const elapsed = Date.now() - start;
        const remaining = MIN_LOADING_MS - elapsed;
        if (remaining > 0) await new Promise((r) => setTimeout(r, remaining));
        if (cancelled) return;

        fadeTo("dashboard", () => {
          setVendorData(result.data);
          setVendorId(vendorParam);
        });
      } catch (err) {
        if (cancelled) return;

        // Show the loading screen for at least a moment before redirecting.
        const elapsed = Date.now() - start;
        const remaining = Math.max(0, 1000 - elapsed);
        if (remaining > 0) await new Promise((r) => setTimeout(r, remaining));
        if (cancelled) return;

        // Hand the error message to the !vendorParam branch and clear the URL.
        // That branch owns the fade-back-to-entry transition to avoid conflicts
        // between two simultaneous fadeTo calls.
        pendingErrorRef.current =
          err.message && err.message !== "API request failed"
            ? err.message
            : "Vendor not found. Please check the name and try again.";
        navigate("/", { replace: true });
      }
    };

    runFetch();
    return () => {
      cancelled = true;
    };
  }, [vendorParam, fadeTo, navigate]);

  // ── VendorEntry submit handler ──────────────────────────────────────────────
  // Nothing async here — just push the vendor name into the URL.
  // The useEffect above reacts to the URL change and drives the entire fetch
  // + transition sequence.
  const handleSearch = (vendorName) => {
    navigate(`/dashboard?vendor=${encodeURIComponent(vendorName)}`);
  };

  const renderPhase = () => {
    switch (phase) {
      case "entry":
        return <VendorEntry onSearch={handleSearch} error={entryError} />;
      case "loading":
        return <LoadingScreen vendorName={vendorParam} />;
      case "dashboard":
        return (
          <Dashboard
            initialVendorId={vendorId}
            initialVendorData={vendorData}
          />
        );
      default:
        return <VendorEntry onSearch={handleSearch} error={entryError} />;
    }
  };

  return (
    <div
      className="h-screen overflow-hidden"
      style={{
        opacity: visible ? 1 : 0,
        transition: `opacity ${FADE_DURATION}ms ease`,
      }}
    >
      {renderPhase()}
    </div>
  );
}
