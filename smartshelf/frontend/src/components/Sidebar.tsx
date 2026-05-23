import { useState } from "react";
import type { ReactNode } from "react";
import { LayoutDashboard, BookOpen, Bookmark, History, Sparkles, LogOut, Shield } from "lucide-react";
import { useAuth } from "../AuthContext";

interface NavProps {
  page: string;
  setPage: (p: string) => void;
  onNavigate?: () => void;
}

interface MobileNavLinkProps {
  to: string;
  children: ReactNode;
  onClick: () => void;
  className?: string;
}

const NAV_ITEMS = [
  { id: "dashboard",       Icon: LayoutDashboard, label: "Dashboard"   },
  { id: "books",           Icon: BookOpen,        label: "Browse Books" },
  { id: "borrowed",        Icon: Bookmark,        label: "My Books"     },
  { id: "history",         Icon: History,         label: "History"      },
  { id: "recommendations", Icon: Sparkles,        label: "For You", badge: "AI" },
];

export default function Sidebar({ page, setPage, onNavigate }: NavProps) {
  const { user, logout } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);
  const selectPage = (id: string) => {
    setPage(id);
    setMobileOpen(false);
    onNavigate?.();
  };

  const NavLink = ({ to, children, onClick, className = "" }: MobileNavLinkProps) => {
    const id = to.replace("/", "") || "dashboard";
    const activeClass = page === id ? "active" : "";
    return (
      <button
        type="button"
        className={`${activeClass} ${className}`.trim()}
        onClick={onClick}
      >
        {children}
      </button>
    );
  };

  const TopNavbar = () => (
    <div className="top-navbar">
      <div className="top-navbar-brand">
        <div className="top-navbar-logo">S</div>
        <span className="top-navbar-name">SmartShelf AI</span>
      </div>
      <button
        type="button"
        className="hamburger-btn"
        onClick={() => setMobileOpen(!mobileOpen)}
      >
        {mobileOpen ? "✕" : "☰"}
      </button>
    </div>
  );

  return (
    <>
      <TopNavbar />

      {mobileOpen && (
        <div className="mob-overlay" onClick={() => setMobileOpen(false)}>
          <div className="mob-panel" onClick={(e) => e.stopPropagation()}>
            <div className="mob-menu-label">MENU</div>
            <nav>
              <NavLink to="/dashboard" onClick={() => selectPage("dashboard")}>
                <LayoutDashboard size={16} />
                <span>Dashboard</span>
              </NavLink>
              <NavLink to="/books" onClick={() => selectPage("books")}>
                <BookOpen size={16} />
                <span>Browse Books</span>
              </NavLink>
              <NavLink to="/borrowed" onClick={() => selectPage("borrowed")}>
                <Bookmark size={16} />
                <span>My Books</span>
              </NavLink>
              <NavLink to="/history" onClick={() => selectPage("history")}>
                <History size={16} />
                <span>History</span>
              </NavLink>
              <NavLink to="/recommendations" onClick={() => selectPage("recommendations")}>
                <Sparkles size={16} />
                <span>For You</span>
              </NavLink>
            </nav>
            <div className="mob-user">
              <span>{user?.name}</span>
              <span>{user?.email}</span>
            </div>
            <button onClick={() => { logout(); setMobileOpen(false); }}>Sign Out</button>
          </div>
        </div>
      )}

      <aside className="sidebar">
        <nav className="sidebar-nav">
          <div className="nav-section-label">MENU</div>
          {NAV_ITEMS.map((item) => (
            <button
              key={item.id}
              className={`nav-item ${page === item.id ? "active" : ""}`}
              onClick={() => selectPage(item.id)}
            >
              <span className="nav-icon">
                <item.Icon size={19} strokeWidth={1.8} />
              </span>
              <span className="nav-label">{item.label}</span>
              {item.badge && <span className="nav-badge">{item.badge}</span>}
            </button>
          ))}
          {user?.is_admin && (
            <button
              className={`nav-item ${page === "admin" ? "active" : ""}`}
              onClick={() => selectPage("admin")}
            >
              <span className="nav-icon">
                <Shield size={19} strokeWidth={1.8} />
              </span>
              <span className="nav-label">Admin</span>
            </button>
          )}
        </nav>

        <div className="sidebar-footer">
          <div className="user-card">
            <div className="user-avatar">{user?.name?.[0]?.toUpperCase()}</div>
            <div className="user-details">
              <div className="user-name">{user?.name}</div>
              <div className="user-email">{user?.email}</div>
            </div>
          </div>
          <button className="btn-logout" onClick={logout}>
            <LogOut size={15} strokeWidth={1.8} />
            Sign Out
          </button>
        </div>
      </aside>
    </>
  );
}
