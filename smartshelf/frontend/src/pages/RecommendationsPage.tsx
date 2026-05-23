import { useEffect, useState } from "react";
import { Sparkles, Bot } from "lucide-react";
import { api } from "../api";
import { useAuth } from "../AuthContext";
import { Recommendation } from "../types";
import EmptyState from "../components/EmptyState";

const FEATURED_CATEGORIES = ["Data Science", "AI/ML", "Cybersecurity", "Web Development"];

interface RecommendationsPageProps {
  setPage: (p: string) => void;
}

export default function RecommendationsPage({ setPage }: RecommendationsPageProps) {
  const { user } = useAuth();
  const [recs, setRecs] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState("");

  const loadRecommendations = async () => {
    if (!user) return;
    setLoading(true);
    try {
      const recData = await api.recommendations();
      if (recData.success && recData.data?.recommendations) {
        setRecs(recData.data.recommendations);
      } else {
        setRecs([]);
      }
    } catch {
      setRecs([]);
    }
    setLoading(false);
  };

  useEffect(() => {
    loadRecommendations();
  }, [user]);

  const navigateToBooks = () => {
    setPage("books");
  };

  const handleBorrow = async (rec: Recommendation) => {
    if (!user) return;
    const res = await api.borrow(rec.id);
    if (res.success) {
      setToast(`Payment ₹${rec.price} successful! "${rec.title}" borrowed.`);
      setTimeout(() => setToast(""), 3000);
      await loadRecommendations();
    } else {
      setToast(res.error || "Error");
      setTimeout(() => setToast(""), 3000);
    }
  };

  return (
    <div className="page">
      {toast && <div className="toast success">{toast}</div>}

      <div className="page-header">
        <h1>
          <Sparkles size={22} strokeWidth={1.8} style={{ display: "inline", marginRight: 8, verticalAlign: "middle" }} />
          AI Recommendations
        </h1>
      </div>

      <div className="ai-badge">
        <Bot size={18} strokeWidth={1.8} />
        <span>SmartShelf AI analyses your reading patterns to find books you'll love</span>
      </div>

      {loading ? (
        <div className="onboarding-skeleton-grid" aria-label="Loading recommendations">
          {[1, 2, 3].map((item) => (
            <div className="onboarding-skeleton-card" key={item}>
              <span />
              <strong />
              <p />
              <div />
            </div>
          ))}
        </div>
      ) : recs.length === 0 ? (
        <EmptyState
          title="Personalized recommendations start here"
          subtitle="Browse books to unlock AI-powered suggestions tailored for you."
          action={{ label: "Browse Books", onClick: navigateToBooks }}
          meta={[
            { value: "AI", label: "Recommendation Engine" },
            { value: "4", label: "Trending Categories" },
            { value: "80+", label: "Books Available" },
          ]}
        >
          <div className="onboarding-trending" aria-label="Featured categories">
            <div className="onboarding-section-label">Featured categories</div>
            <div className="onboarding-trending-grid">
              {FEATURED_CATEGORIES.map((category) => (
                <button type="button" key={category} onClick={navigateToBooks}>
                  {category}
                </button>
              ))}
            </div>
          </div>
        </EmptyState>
      ) : (
        <div className="recs-grid">
          {recs.map((rec, i) => (
            <div key={rec.id} className="rec-card">
              <div className="rec-rank">#{i + 1}</div>
              <div className="rec-info">
                <span className="book-category">{rec.category}</span>
                <h3>{rec.title}</h3>
                <p className="book-author">by {rec.author}</p>

                {rec.similarity_score > 0 && (
                  <div className="similarity-bar">
                    <div className="similarity-label">
                      AI Match: {Math.round(rec.similarity_score * 100)}%
                    </div>
                    <div className="bar-track">
                      <div
                        className="bar-fill"
                        style={{ width: `${Math.min(rec.similarity_score * 100, 100)}%` }}
                      />
                    </div>
                  </div>
                )}

                <div className="rec-footer">
                  <span className="book-price">₹{rec.price}/mo</span>
                  <button
                    type="button"
                    className="btn-borrow-now"
                    onClick={navigateToBooks}
                  >
                    Borrow Now
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
