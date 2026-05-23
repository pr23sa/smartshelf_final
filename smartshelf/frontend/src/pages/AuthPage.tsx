import { useState, useEffect } from "react";
import { api } from "../api";
import { useAuth } from "../AuthContext";

export default function AuthPage() {
  const { setAuth } = useAuth();
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [isLogin, setIsLogin] = useState(true);
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [mounted, setMounted] = useState(false);
  const [authOpen, setAuthOpen] = useState(false);
  const [showMobileForm, setShowMobileForm] = useState(false);

  const [backendReady, setBackendReady] = useState(false);

useEffect(() => {
  const wake = async () => {
    try {
      await fetch("https://smartshelf-backend.onrender.com/api/health");
    } catch {}
    finally {
      setBackendReady(true);
    }
  };
  wake();
}, []);

if (!backendReady) return (
  <div style={{display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center',height:'100vh',gap:'12px'}}>
    <div style={{fontSize:'24px'}}>📚</div>
    <div style={{fontSize:'16px',fontWeight:600,color:'#1a1a2e'}}>Starting SmartShelf...</div>
    <div style={{fontSize:'13px',color:'#6b7280'}}>First load takes ~30 seconds. Please wait.</div>
  </div>
);

  useEffect(() => {
    const t = setTimeout(() => setMounted(true), 50);
    return () => clearTimeout(t);
  }, []);

  const update = (k: string, v: string) => setForm((f) => ({ ...f, [k]: v }));

  const submit = async (nextIsLogin = isLogin) => {
    setError("");
    setLoading(true);
    try {
      let res: any;
      if (!nextIsLogin) {
        res = await api.signup(form.name, form.email, form.password);
      } else {
        res = await api.login(form.email, form.password);
      }
      if (res.success && res.data) {
        setAuth(res.data.user, res.data.token);
        window.history.replaceState(null, "", "/dashboard");
      } else {
        setError(res.error || "Something went wrong");
      }
    } catch {
      setError("Cannot connect to server. Is the backend running?");
    }
    setLoading(false);
  };

  const showLogin = () => {
    setIsLogin(true);
    setMode("login");
    setError("");
  };

  const showSignup = () => {
    setIsLogin(false);
    setMode("signup");
    setError("");
  };

  const authFormFields = (
    <form className="auth-form" onSubmit={(e) => { e.preventDefault(); submit(isLogin); }}>
      {!isLogin && (
        <div className="field field-animate" style={{ animationDelay: "0ms" }}>
          <label>Full Name</label>
          <input
            type="text"
            placeholder="Full name"
            value={form.name}
            onChange={(e) => update("name", e.target.value)}
          />
        </div>
      )}
      <div className="field field-animate" style={{ animationDelay: "60ms" }}>
        <label>Email Address</label>
        <input
          type="email"
          placeholder="Email address"
          value={form.email}
          onChange={(e) => update("email", e.target.value)}
        />
      </div>
      <div className="field field-animate" style={{ animationDelay: "120ms" }}>
        <label>Password</label>
        <input
          type="password"
          placeholder="Password"
          value={form.password}
          onChange={(e) => update("password", e.target.value)}
        />
      </div>

      {error && (
        <div className="auth-error">
          {error}
        </div>
      )}

      <button
        type="submit"
        className="btn-primary btn-auth"
        disabled={loading}
        style={{ animationDelay: "180ms" }}
      >
        {loading ? (
          <span className="btn-loading">
            <span className="btn-spinner" />
            Please wait...
          </span>
        ) : (
          isLogin ? "Login" : "Create Account"
        )}
      </button>
    </form>
  );

  const authForm = (
    <>
      <div className="auth-card-header">
        <h1>
          {isLogin ? "Welcome back" : "Create account"}
        </h1>
        <p>
          {isLogin
            ? "Sign in to access your library"
            : "Join SmartShelf and start reading"}
        </p>
      </div>

      <div className="auth-tabs">
        <button
          type="button"
          data-tab="signin"
          className={isLogin ? "active" : ""}
          onClick={showLogin}
        >
          Login
        </button>
        <button
          type="button"
          data-tab="signup"
          className={!isLogin ? "active" : ""}
          onClick={showSignup}
        >
          Sign Up
        </button>
      </div>

      {authFormFields}
    </>
  );

  return (
    <div className={`auth-page ${mounted ? "auth-mounted" : ""}`} onClick={() => setAuthOpen(false)}>
      <div className="auth-mobile-navbar">
        <div className="auth-mobile-brand">
          <div className="auth-mobile-logo">S</div>
          <span>SmartShelf AI</span>
        </div>
      </div>

      <div className="auth-left left-panel hero-section">

        <div className="auth-left-gradient-layer" aria-hidden="true" />
        <div className="auth-float-book" aria-hidden="true">
          <svg viewBox="0 0 120 140" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M10 8C10 4.686 12.686 2 16 2h40v136H16c-3.314 0-6-2.686-6-6V8z" fill="rgba(58,86,212,0.06)" stroke="rgba(58,86,212,0.12)" strokeWidth="1.5" />
            <path d="M56 2h48c3.314 0 6 2.686 6 6v124c0 3.314-2.686 6-6 6H56V2z" fill="rgba(98,114,236,0.04)" stroke="rgba(58,86,212,0.1)" strokeWidth="1.5" />
            <line x1="56" y1="2" x2="56" y2="138" stroke="rgba(58,86,212,0.15)" strokeWidth="1.5" />
            <line x1="22" y1="28" x2="44" y2="28" stroke="rgba(58,86,212,0.1)" strokeWidth="2" strokeLinecap="round" />
            <line x1="22" y1="42" x2="40" y2="42" stroke="rgba(58,86,212,0.08)" strokeWidth="2" strokeLinecap="round" />
            <line x1="22" y1="56" x2="44" y2="56" stroke="rgba(58,86,212,0.08)" strokeWidth="2" strokeLinecap="round" />
            <line x1="66" y1="28" x2="98" y2="28" stroke="rgba(58,86,212,0.08)" strokeWidth="2" strokeLinecap="round" />
            <line x1="66" y1="42" x2="94" y2="42" stroke="rgba(58,86,212,0.06)" strokeWidth="2" strokeLinecap="round" />
          </svg>
        </div>

        <div className="auth-left-inner">

          <div className="auth-brand">
            <div className="auth-brand-mark">S</div>
            <span className="auth-brand-name">SmartShelf AI</span>
          </div>

          <div className="auth-left-copy">
            <h2 className="hero-title">The smarter way to manage your library</h2>
            <p className="hero-subtitle">
              Borrow books, track history, and get personalised
              AI recommendations - all in one place.
            </p>
          </div>

          <ul className="auth-features feature-list">
            <li className="auth-feature-item" style={{ opacity: 1, transform: "translateX(0)" }}>
              <div className="auth-feature-icon">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
              </div>
              <div>
                <strong>80+ Curated Books</strong>
                <span>Handpicked across Tech, Data Science, AI/ML and Cybersecurity</span>
              </div>
            </li>
            <li className="auth-feature-item" style={{ opacity: 1, transform: "translateX(0)" }}>
              <div className="auth-feature-icon">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
              </div>
              <div>
                <strong>Soft Copy Available</strong>
                <span>Read online for free or download PDFs instantly</span>
              </div>
            </li>
            <li className="auth-feature-item">
              <div className="auth-feature-icon">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
              </div>
              <div>
                <strong>Hard Copy Reservation</strong>
                <span>Reserve physical books and collect from library within 24 hours</span>
              </div>
            </li>
            <li className="auth-feature-item">
              <div className="auth-feature-icon">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
              </div>
              <div>
                <strong>AI Recommendations</strong>
                <span>Get personalised book suggestions based on your reading history</span>
              </div>
            </li>
            <li className="auth-feature-item">
              <div className="auth-feature-icon">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
              </div>
              <div>
                <strong>Full Borrow History</strong>
                <span>Track every book borrowed, due dates and return status</span>
              </div>
            </li>
          </ul>

          <div className="auth-stats stats-row">
            <div className="auth-stat">
              <span className="auth-stat-value">80+</span>
              <span className="auth-stat-label">Books</span>
            </div>
            <div className="auth-stat-divider" />
            <div className="auth-stat">
              <span className="auth-stat-value">500+</span>
              <span className="auth-stat-label">Users</span>
            </div>
            <div className="auth-stat-divider" />
            <div className="auth-stat">
              <span className="auth-stat-value">AI</span>
              <span className="auth-stat-label">Powered</span>
            </div>
          </div>

          <div className="mobile-auth-btns">
            <button className="mobile-btn-login" onClick={() => { setIsLogin(true); setShowMobileForm(true); }}>
              Login
            </button>
            <button className="mobile-btn-signup" onClick={() => { setIsLogin(false); setShowMobileForm(true); }}>
              Sign Up
            </button>
          </div>

        </div>
      </div>

      <div className="auth-right" onClick={(e) => e.stopPropagation()}>
        <div className="mobile-logo">
          <div className="logo-icon">S</div>
          <span>SmartShelf AI</span>
        </div>
        <div className={`auth-card ${authOpen ? "active" : ""}`} onClick={(e) => e.stopPropagation()}>
          {authForm}
        </div>
      </div>

      {showMobileForm && (
        <div className="mobile-sheet-overlay" onClick={() => setShowMobileForm(false)}>
          <div className="mobile-sheet" onClick={(e) => e.stopPropagation()}>
            <div className="sheet-handle" />
            <button className="sheet-close" onClick={() => setShowMobileForm(false)}>✕</button>
            <h3>{isLogin ? "Login" : "Sign Up"}</h3>
            <div className="sheet-tabs">
              <button className={isLogin ? "active" : ""} onClick={() => setIsLogin(true)} type="button">Login</button>
              <button className={!isLogin ? "active" : ""} onClick={() => setIsLogin(false)} type="button">Sign Up</button>
            </div>
            {authFormFields}
          </div>
        </div>
      )}

    </div>
  );
}


