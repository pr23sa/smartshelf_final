import { useEffect, useState } from "react";
import { Bookmark, CheckCircle2, ArrowLeftRight, Sparkles, BookOpen, History, CalendarDays, Lightbulb } from "lucide-react";
import { useAuth } from "../AuthContext";
import { API_BASE_URL, api } from "../api";
import { Recommendation } from "../types";

interface DashboardProps {
  setPage: (p: string) => void;
}

const READING_TIPS = [
  "Read before bed to improve sleep quality",
  "Start the week with 20 pages a day",
  "Try a genre outside your comfort zone",
  "Take notes while reading to retain more",
  "Re-read a favourite chapter this week",
  "Share a book recommendation with a friend",
  "Perfect day for a long reading session",
];

export default function Dashboard({ setPage }: DashboardProps) {
  const { user } = useAuth();
  const [stats, setStats] = useState({ borrowed: 0, returned: 0, total: 0 });
  const [recs, setRecs] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) return;
    Promise.all([
      fetch(`${API_BASE_URL}/api/borrowed/${user.id}`).then((res) => res.json()),
      api.recommendations(),
    ]).then(([borrowedRes, rRes]) => {
      if (borrowedRes.success) {
        const borrows = borrowedRes.borrows || [];
        const borrowed = borrows.filter((h: any) => h.status === "borrowed").length;
        const returned = borrows.filter((h: any) => h.status === "returned").length;
        setStats({ borrowed, returned, total: borrows.length });
      }
      if (rRes.success && rRes.data) {
        setRecs(rRes.data.recommendations.slice(0, 3));
      }
      setLoading(false);
    });
  }, [user]);

  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";

  const firstName =
    (user?.name?.split(" ")[0]?.charAt(0).toUpperCase() ?? "") +
    (user?.name?.split(" ")[0]?.slice(1) ?? "");

  const today = new Date();
  const formattedDate = today.toLocaleDateString("en-GB", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  });
  const readingTip = READING_TIPS[today.getDay()];

  return (
    <div className="page">

      {/* ── Hero Banner ── */}
      <div className="dashboard-hero">
        <div className="hero-dots" aria-hidden="true" />
        <div className="hero-circle-1" aria-hidden="true" />
        <div className="hero-circle-2" aria-hidden="true" />

        <div className="hero-left">
          <div className="hero-eyebrow">
            Your Library Dashboard
          </div>
          <h1 className="dashboard-greeting">
            {greeting}, {firstName}!
          </h1>
          <p className="dashboard-sub">Here's what's happening with your reading journey.</p>
          <div className="hero-actions">
            <button className="hero-btn-primary" onClick={() => setPage("books")}>
              Browse Books →
            </button>
            <button className="hero-btn-secondary" onClick={() => setPage("recommendations")}>
              ✦ AI Picks for You
            </button>
          </div>
        </div>

        <div className="hero-right">
          <div className="hero-tip-card">
            <div className="hero-tip-date">
              <CalendarDays size={14} strokeWidth={1.8} />
              <span>{formattedDate}</span>
            </div>
            <div className="hero-tip-divider" />
            <div className="hero-tip-body">
              <div className="hero-tip-label">
                <Lightbulb size={12} strokeWidth={1.8} />
                Reading Tip
              </div>
              <p className="hero-tip-text">{readingTip}</p>
            </div>
          </div>
        </div>
      </div>

      {/* ── About SmartShelf ── */}
      <section className="about-smartshelf">
        <div className="about-panel">
          <div className="about-panel-item">
            <div className="about-panel-icon about-panel-icon--blue">
              <BookOpen size={18} strokeWidth={1.8} />
            </div>
            <div className="about-panel-title">Curated Library</div>
            <p className="about-panel-sub">
              80+ books handpicked across Tech, Data Science, AI/ML and Cybersecurity
            </p>
          </div>
          <div className="about-panel-divider" aria-hidden="true" />
          <div className="about-panel-item">
            <div className="about-panel-icon about-panel-icon--purple">
              <Sparkles size={18} strokeWidth={1.8} />
            </div>
            <div className="about-panel-title">Smart Recommendations</div>
            <p className="about-panel-sub">
              The more you read, the better we get at finding your next favourite book
            </p>
          </div>
          <div className="about-panel-divider" aria-hidden="true" />
          <div className="about-panel-item">
            <div className="about-panel-icon about-panel-icon--green">
              <History size={18} strokeWidth={1.8} />
            </div>
            <div className="about-panel-title">Track Everything</div>
            <p className="about-panel-sub">
              Your full borrowing history, always organised and easy to revisit
            </p>
          </div>
        </div>
      </section>

      {/* ── Stats ── */}
      <div className="stats-bar">
        <button type="button" className="stats-bar-item" onClick={() => setPage("borrowed")}>
          <div className="stats-bar-icon"><Bookmark size={18} strokeWidth={1.7} /></div>
          <div className="stats-bar-value">{stats.borrowed}</div>
          <div className="stats-bar-label">
            Currently Borrowed <span className="stats-bar-arrow">→</span>
          </div>
        </button>
        <div className="stats-bar-divider" aria-hidden="true" />
        <button type="button" className="stats-bar-item" onClick={() => setPage("history")}>
          <div className="stats-bar-icon"><CheckCircle2 size={18} strokeWidth={1.7} /></div>
          <div className="stats-bar-value">{stats.returned}</div>
          <div className="stats-bar-label">
            Books Returned <span className="stats-bar-arrow">→</span>
          </div>
        </button>
        <div className="stats-bar-divider" aria-hidden="true" />
        <button type="button" className="stats-bar-item" onClick={() => setPage("history")}>
          <div className="stats-bar-icon"><ArrowLeftRight size={18} strokeWidth={1.7} /></div>
          <div className="stats-bar-value">{stats.total}</div>
          <div className="stats-bar-label">
            Total Transactions <span className="stats-bar-arrow">→</span>
          </div>
        </button>
        <div className="stats-bar-divider" aria-hidden="true" />
        <button type="button" className="stats-bar-item" onClick={() => setPage("recommendations")}>
          <div className="stats-bar-icon"><Sparkles size={18} strokeWidth={1.7} /></div>
          <div className="stats-bar-value">{recs.length}</div>
          <div className="stats-bar-label">
            AI Picks for You <span className="stats-bar-arrow">→</span>
          </div>
        </button>
      </div>

      {/* ── AI Recommendations ── */}
      {!loading && recs.length > 0 && (
        <div className="dashboard-section">
          <div className="section-header">
            <h2>
              <Sparkles size={18} strokeWidth={1.8} style={{ display: "inline", marginRight: 6, verticalAlign: "middle" }} />
              AI Recommendations
            </h2>
            <button className="btn-link" onClick={() => setPage("recommendations")}>
              View all →
            </button>
          </div>
          <div className="rec-preview">
            {recs.map((r) => (
              <div key={r.id} className="rec-mini-card">
                <div>
                  <div className="rec-mini-title">{r.title}</div>
                  <div className="rec-mini-author">{r.author}</div>
                  <div className="rec-mini-score">
                    {r.similarity_score > 0
                      ? `${Math.round(r.similarity_score * 100)}% match`
                      : r.category}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {!loading && recs.length === 0 && (
        <div className="empty-state">
          <div className="empty-icon"><BookOpen size={48} strokeWidth={1.4} /></div>
          <h3>Start your reading journey!</h3>
          <p>Borrow a few books to get personalized AI recommendations.</p>
          <button className="btn-primary" onClick={() => setPage("books")}>
            Browse Books
          </button>
        </div>
      )}
    </div>
  );
}
