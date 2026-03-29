import Sidebar from "./Sidebar";
import TopBar from "./TopBar";

export default function Layout({ children, activeTab, onTabChange, vendor }) {
  return (
    <div className="flex h-screen bg-pg-base overflow-hidden relative">
      {/* Background grid */}
      <div
        className="fixed inset-0 opacity-[0.05] pointer-events-none"
        style={{
          backgroundImage:
            "linear-gradient(#2E2E9E 4px, transparent 1px), linear-gradient(90deg, #2E2E9E 4px, transparent 1px)",
          backgroundSize: "60px 60px",
        }}
      />
      <Sidebar activeTab={activeTab} onTabChange={onTabChange} />
      <div className="flex-1 flex flex-col overflow-hidden">
        <TopBar activeTab={activeTab} vendor={vendor} />
        <main className="flex-1 overflow-y-auto p-6 bg-pg-base">
          {children}
        </main>
      </div>
    </div>
  );
}
