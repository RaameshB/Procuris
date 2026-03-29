import Sidebar from "./Sidebar";
import TopBar from "./TopBar";

export default function Layout({ children, activeTab, onTabChange, vendor }) {
  return (
    <div className="flex h-screen bg-pg-base overflow-hidden">
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
