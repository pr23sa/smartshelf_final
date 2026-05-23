import { useEffect, useState } from "react";
import { api } from "../api";
import { Book } from "../types";
import { useAuth } from "../AuthContext";
import BookCard from "../components/BookCard";

const CATEGORIES = ["All", "Web Development", "Data Science", "AI/ML", "Cybersecurity"];

export default function BooksPage() {
  const { user } = useAuth();
  const [books, setBooks] = useState<Book[]>([]);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("All");
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [toast, setToast] = useState("");
  const [toastType, setToastType] = useState<"success" | "error">("success");

  const loadData = async () => {
    if (!user) return;
    setLoading(true);
    setLoadError("");
    const bRes = await api.books();
    if (bRes.success && bRes.data) {
      setBooks(bRes.data.books);
    } else {
      setLoadError(
        bRes.error || "Could not connect to server. Make sure the backend is running."
      );
    }
    setLoading(false);
  };

  useEffect(() => {
    loadData();
  }, [user]);

  const showToast = (msg: string, type: "success" | "error" = "success") => {
    setToast(msg);
    setToastType(type);
    setTimeout(() => setToast(""), 3000);
  };

  const filtered = books.filter((b) => {
    const matchCat = category === "All" || b.category === category;
    const matchSearch =
      b.title.toLowerCase().includes(search.toLowerCase()) ||
      b.author.toLowerCase().includes(search.toLowerCase());
    return matchCat && matchSearch;
  });

  return (
    <div className="page">
      {toast && <div className={`toast ${toastType}`}>{toast}</div>}

      <div className="page-header">
        <h1>Browse Library</h1>
        <p>Read free online, download PDFs, or reserve a physical copy</p>
      </div>

      <div className="filters">
        <div className="search-wrap">
          <span className="search-icon">&#128269;</span>
          <input
            type="text"
            placeholder="Search by title or author..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="search-input"
          />
        </div>
        <div className="category-tabs">
          {CATEGORIES.map((cat) => (
            <button
              key={cat}
              className={`cat-tab ${category === cat ? "active" : ""}`}
              onClick={() => setCategory(cat)}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="loading-state">
          <div className="spinner" />
          <p>Loading books...</p>
        </div>
      ) : loadError ? (
        <div className="empty-state">
          <div className="empty-icon">!</div>
          <h3>Could not load books</h3>
          <p>{loadError}</p>
          <button type="button" className="btn-primary" style={{ marginTop: 16 }} onClick={loadData}>
            Try again
          </button>
        </div>
      ) : (
        <>
          <p className="result-count">
            {filtered.length} book{filtered.length !== 1 ? "s" : ""} found
          </p>
          <div className="books-grid">
            {filtered.map((book) => (
              <BookCard key={book.id} book={book} onToast={showToast} actionMode="browse" />
            ))}
          </div>
          {filtered.length === 0 && (
            <div className="empty-state">
              <div className="empty-icon">?</div>
              <h3>No books found</h3>
              <p>Try a different search or category.</p>
            </div>
          )}
        </>
      )}
    </div>
  );
}
