import { useState, useCallback } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Login from "./pages/Login";
import VendorEntry from "./pages/VendorEntry";
import LoadingScreen from "./pages/LoadingScreen";
import Dashboard from "./pages/Dashboard";
import { apiFetch } from "./api";

const FADE_DURATION = 350; // ms – matches CSS transition
const MIN_LOADING_MS = 1600; // minimum time to show the loading screen

function AppFlow() {
  const [phase, setPhase] = useState("entry"); // "entry" | "loading" | "dashboard"
  const [visible, setVisible] = useState(true); // drives opacity transition
  const [vendorData, setVendorData] = useState(null);
  const [pendingVendorName, setPendingVendorName] = useState(null);
  const [vendorId, setVendorId] = useState(null);
  const [entryError, setEntryError] = useState(null);
  const [isSearching, setIsSearching] = useState(false);

  /**
   * Fade the current screen out, swap to nextPhase, then fade back in.
   * `setup` is called just before the phase swap so state is ready
   * when the new component first renders.
   */
  const fadeTo = useCallback((nextPhase, setup) => {
    setVisible(false);
    setTimeout(() => {
      setup?.();
      setPhase(nextPhase);
      // Give React one frame to mount/update the new component at opacity-0
      // before we start the fade-in transition.
      requestAnimationFrame(() => setVisible(true));
    }, FADE_DURATION);
  }, []);

  const handleSearch = async (vendorName) => {
    if (isSearching) return;
    setIsSearching(true);
    setEntryError(null);
    setPendingVendorName(vendorName);

    // Begin fading to loading screen immediately
    fadeTo("loading");

    const start = Date.now();

    try {
      const result = await apiFetch(`/api/vendor/${vendorName}`);

      // Ensure the loading screen is shown for at least MIN_LOADING_MS
      const elapsed = Date.now() - start;
      const remaining = MIN_LOADING_MS - elapsed;
      if (remaining > 0) await new Promise((r) => setTimeout(r, remaining));

      fadeTo("dashboard", () => {
        setVendorData(result.data);
        setVendorId(vendorName);
      });
    } catch (err) {
      // Show the loading screen for at least a moment before snapping back
      const elapsed = Date.now() - start;
      const remaining = Math.max(0, 1000 - elapsed);
      if (remaining > 0) await new Promise((r) => setTimeout(r, remaining));

      fadeTo("entry", () => {
        setEntryError(
          err.message && err.message !== "API request failed"
            ? err.message
            : "Vendor not found. Please check the name and try again.",
        );
      });
    } finally {
      setIsSearching(false);
    }
  };

  const renderPhase = () => {
    switch (phase) {
      case "entry":
        return (
          <VendorEntry
            onSearch={handleSearch}
            error={entryError}
            isSearching={isSearching}
          />
        );
      case "loading":
        return <LoadingScreen vendorName={pendingVendorName} />;
      case "dashboard":
        return (
          <Dashboard
            initialVendorId={vendorId}
            initialVendorData={vendorData}
          />
        );
      default:
        return (
          <VendorEntry
            onSearch={handleSearch}
            error={entryError}
            isSearching={isSearching}
          />
        );
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

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Standalone login page – not part of the vendor-entry flow */}
        <Route path="/login" element={<Login />} />

        {/* Everything else goes through the phase-based app flow */}
        <Route path="/*" element={<AppFlow />} />
      </Routes>
    </BrowserRouter>
  );
}
