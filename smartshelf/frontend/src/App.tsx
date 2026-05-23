import { useEffect, useState } from "react";
import { AuthProvider, useAuth } from "./AuthContext";
import AuthPage from "./pages/AuthPage";
import Dashboard from "./pages/Dashboard";
import BooksPage from "./pages/BooksPage";
import BorrowedPage from "./pages/BorrowedPage";
import HistoryPage from "./pages/HistoryPage";
import RecommendationsPage from "./pages/RecommendationsPage";
import AdminPage from "./pages/AdminPage";
import Sidebar from "./components/Sidebar";
import { Menu, X } from "lucide-react";
import "./App.css";

function AppContent() {
  const { user } = useAuth();
  const [page, setPage] = useState("dashboard");
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    if (!user) {
      window.history.replaceState(null, "", "/auth");
      return;
    }
    const knownPaths = new Set(["/", "/auth", "/dashboard"]);
    if (!knownPaths.has(window.location.pathname) || window.location.pathname === "/" || window.location.pathname === "/auth") {
      window.history.replaceState(null, "", "/dashboard");
    }
  }, [user]);

  if (!user) return <AuthPage />;

  const renderPage = () => {
    switch (page) {
      case "dashboard": return <Dashboard setPage={setPage} />;
      case "books": return <BooksPage />;
      case "borrowed": return <BorrowedPage setPage={setPage} />;
      case "history": return <HistoryPage setPage={setPage} />;
      case "recommendations": return <RecommendationsPage setPage={setPage} />;
      case "admin": return <AdminPage />;
      default: return <Dashboard setPage={setPage} />;
    }
  };

  return (
    <div className={`app-layout ${sidebarOpen ? "sidebar-open" : ""}`}>
      <div className="mobile-navbar">
        <button
          type="button"
          className="mobile-nav-toggle hamburger"
          onClick={() => setSidebarOpen((open) => !open)}
          aria-label={sidebarOpen ? "Close navigation" : "Open navigation"}
          aria-expanded={sidebarOpen}
        >
          {sidebarOpen ? <X size={22} strokeWidth={2} /> : <Menu size={22} strokeWidth={2} />}
        </button>
        <div className="logo-icon">S</div>
        <span className="brand-name">SmartShelf AI</span>
      </div>
      <div className="mobile-sidebar-backdrop" onClick={() => setSidebarOpen(false)} />
      <Sidebar page={page} setPage={setPage} onNavigate={() => setSidebarOpen(false)} />
      <main className="main-content">
        {renderPage()}
      </main>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
