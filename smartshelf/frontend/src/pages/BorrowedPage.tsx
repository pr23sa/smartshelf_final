import { useEffect, useMemo, useState } from "react";
import { API_BASE_URL } from "../api";
import { useAuth } from "../AuthContext";
import EmptyState from "../components/EmptyState";

type MyBookRecord = {
  id: number;
  user_id: number;
  book_id: number;
  title: string;
  author: string;
  category: string;
  pdf_path?: string | null;
  borrow_type: string;
  status: string;
  borrow_date: string | null;
  due_date: string | null;
  reserved_date: string | null;
  pickup_deadline: string | null;
  return_date: string | null;
  amount_paid: number;
  days_overdue: number;
  days_remaining: number | null;
  display_status?: string;
  reservedAt?: string | null;
  pickedUpAt?: string | null;
  dueDate?: string | null;
  returnedAt?: string | null;
  hours_until_pickup: number | null;
  is_overdue: boolean;
};

function daysUntil(date?: string | null) {
  if (!date) return null;
  const due = new Date(date).getTime();
  if (Number.isNaN(due)) return null;
  return Math.ceil((due - Date.now()) / 86400000);
}

function fmtShortDate(date?: string | null) {
  if (!date) return "N/A";
  return new Date(date).toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
  });
}

function fmtDueDate(date?: string | null) {
  if (!date) return "N/A";
  return new Date(date).toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

function pickupLabel(book: MyBookRecord) {
  if (book.pickup_deadline) {
    const deadline = new Date(book.pickup_deadline);
    const today = new Date();
    const tomorrow = new Date();
    tomorrow.setDate(today.getDate() + 1);

    if (deadline.toDateString() === today.toDateString()) return "Today";
    if (deadline.toDateString() === tomorrow.toDateString()) return "Tomorrow";
    return fmtShortDate(book.pickup_deadline);
  }
  return "Tomorrow";
}

function typeLabel(book: MyBookRecord) {
  if (book.borrow_type === "digital" && book.status === "owned") return "Downloaded";
  if (book.borrow_type === "digital") return "Digital";
  return "Hard Copy";
}

function statusLabel(book: MyBookRecord) {
  if (book.status === "owned") return "Owned";
  if (book.status === "reserved") return "Reserved";
  if (book.status === "borrowed") return "Borrowed";
  if (book.status === "returned") return "Returned";
  return "Active";
}

function statusTone(book: MyBookRecord) {
  if (book.status === "reserved") return "info";
  if (book.status === "owned" || book.borrow_type === "digital") return "success";
  return "info";
}

const TRENDING_BOOKS = [
  "Clean Code",
  "Deep Learning",
  "Designing Data-Intensive Applications",
  "The Pragmatic Programmer",
];

interface BorrowedPageProps {
  setPage: (p: string) => void;
}

export default function BorrowedPage({ setPage }: BorrowedPageProps) {
  const { user } = useAuth();
  const [books, setBooks] = useState<MyBookRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState<MyBookRecord | null>(null);

  const loadBorrows = async () => {
    if (!user) return;
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${API_BASE_URL}/api/borrowed/${user.id}`);
      const data = await res.json();
      if (data.success) {
        const current = (data.borrows || []).filter((b: MyBookRecord) =>
          b.status === "reserved" || b.status === "borrowed" || b.status === "owned" || b.borrow_type === "digital",
        );
        setBooks(current);
      } else {
        setError(data.error || "Failed to load your books");
      }
    } catch (err) {
      console.error("Fetch error:", err);
      setError("Could not connect to server");
    }
    setLoading(false);
  };

  useEffect(() => {
    if (!user) return;
    loadBorrows();
  }, [user]);

  const stats = useMemo(() => {
    const activeBorrows = books.filter((b) => b.status === "borrowed").length;
    const digitalOwned = books.filter((b) => b.borrow_type === "digital" || b.status === "owned").length;
    const pendingReturns = books.filter((b) => b.status === "borrowed" && b.borrow_type === "hard copy").length;
    return { total: books.length, activeBorrows, digitalOwned, pendingReturns };
  }, [books]);

  const hasStats = stats.total > 0
    || stats.activeBorrows > 0
    || stats.digitalOwned > 0
    || stats.pendingReturns > 0;

  const handleReturn = async (borrowId: number, bookId: number) => {
    if (!user) return;
    const res = await fetch(`${API_BASE_URL}/api/return`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ borrow_id: borrowId, user_id: user.id, book_id: bookId }),
    });
    const data = await res.json();
    if (data.success) loadBorrows();
  };

  const handlePickup = async (borrowId: number, bookId: number) => {
    if (!user) return;
    const res = await fetch(`${API_BASE_URL}/api/pickup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ borrow_id: borrowId, user_id: user.id, book_id: bookId }),
    });
    const data = await res.json();
    if (data.success) loadBorrows();
    else setError(data.error || "Failed to mark pickup completed");
  };

  const openPdf = (book: MyBookRecord, download = false) => {
    const url = `${API_BASE_URL}/book-pdf/${book.book_id}`;
    if (!download) {
      window.open(url, "_blank", "noopener,noreferrer");
      return;
    }
    const link = document.createElement("a");
    link.href = url;
    link.download = `${book.title.replace(/[^a-zA-Z0-9\s]/g, "").replace(/\s+/g, "_")}.pdf`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="page books-page-shell">
      <div className="library-page-top">
        <div className="page-header">
          <h1>My Books</h1>
          <p>Current reservations, active hard copies, and digital books.</p>
        </div>
        <button className="library-icon-button" onClick={loadBorrows} aria-label="Refresh books">
          Refresh
        </button>
      </div>

      {hasStats && (
        <div className="library-stats-grid">
          <div className="library-stat-card"><span>Total Books</span><strong>{stats.total}</strong></div>
          <div className="library-stat-card"><span>Active Borrows</span><strong>{stats.activeBorrows}</strong></div>
          <div className="library-stat-card"><span>Digital Owned</span><strong>{stats.digitalOwned}</strong></div>
          <div className="library-stat-card"><span>Pending Returns</span><strong>{stats.pendingReturns}</strong></div>
        </div>
      )}

      {loading && (
        <div className="my-books-grid">
          {[1, 2, 3, 4].map((item) => <div className="book-skeleton-card" key={item} />)}
        </div>
      )}
      {error && <div className="library-empty-state error-state">{error}</div>}

      {!loading && !error && books.length === 0 && (
        <EmptyState
          title="Your shelf is waiting"
          subtitle="Browse books and start building your reading journey."
          action={{ label: "Browse Books", onClick: () => setPage("books") }}
          meta={[
            { value: "80+", label: "Books Available" },
            { value: "4", label: "Trending Categories" },
            { value: "AI", label: "Smart Picks" },
          ]}
        >
          <div className="onboarding-trending" aria-label="Trending books">
            <div className="onboarding-section-label">Trending books</div>
            <div className="onboarding-trending-grid">
              {TRENDING_BOOKS.map((title) => (
                <button type="button" key={title} onClick={() => setPage("books")}>
                  {title}
                </button>
              ))}
            </div>
          </div>
        </EmptyState>
      )}

      {!loading && !error && books.length > 0 && (
        <div className="my-books-grid">
          {books.map((book) => {
            const days = daysUntil(book.due_date);
            const daysLeft = book.days_remaining ?? days;
            const isDigital = book.borrow_type === "digital" || book.status === "owned";
            const isHardCopy = book.borrow_type === "hard copy" && book.status === "borrowed";
            const isReserved = book.status === "reserved";
            const metaLine = isHardCopy && daysLeft !== null
              ? `Due: ${fmtShortDate(book.due_date)} • ${
                  book.is_overdue ? `${book.days_overdue} days late` : `${Math.max(daysLeft, 0)} days left`
                }`
              : isReserved
                ? `Pickup: ${pickupLabel(book)}`
                : isDigital
                  ? "Owned"
                  : book.category;
            return (
              <article className="my-book-card" key={book.id}>
                <div className="my-book-content">
                  <div className="my-book-badges">
                    <span className={`library-chip type-${book.borrow_type === "digital" ? "digital" : book.status}`}>
                      {typeLabel(book)}
                    </span>
                    <span className={`library-chip ${statusTone(book)}`}>{statusLabel(book)}</span>
                  </div>
                  <h2>{book.title}</h2>
                  <p>{book.author}</p>
                  {isHardCopy && daysLeft !== null ? (
                    <div className="flex flex-col">
                      <p className="text-base font-medium text-slate-900">
                        Due on {fmtDueDate(book.due_date)}
                      </p>
                      <span className="text-sm text-slate-500 mt-1">
                        {book.is_overdue ? `${book.days_overdue} days late` : `${Math.max(daysLeft, 0)} days left`}
                      </span>
                    </div>
                  ) : (
                    <div className="my-book-meta">{metaLine}</div>
                  )}
                  {isReserved && (
                    <div className="pickup-info-box">
                      Please visit the library and collect your book within 24 hours using your Reservation ID.
                    </div>
                  )}

                  <div className="my-book-actions">
                    {isDigital && (
                      <>
                        <button className="primary-action" onClick={() => openPdf(book)}>Read</button>
                        <button onClick={() => openPdf(book, true)}>Download</button>
                      </>
                    )}
                    {isHardCopy && (
                      <button className="primary-action" onClick={() => handleReturn(book.id, book.book_id)}>Return</button>
                    )}
                    {isReserved && (
                      <button className="primary-action" onClick={() => handlePickup(book.id, book.book_id)}>Mark Picked Up</button>
                    )}
                    <button onClick={() => setSelected(book)}>Details</button>
                  </div>
                </div>
              </article>
            );
          })}
        </div>
      )}

      {selected && (
        <div className="details-overlay" onClick={() => setSelected(null)}>
          <div className="details-modal" onClick={(event) => event.stopPropagation()}>
            <div>
              <span className={`library-chip ${statusTone(selected)}`}>{statusLabel(selected)}</span>
              <h2>{selected.title}</h2>
              <p>{selected.author}</p>
            </div>
            <div className="details-modal-grid">
              <span>Type</span><strong>{typeLabel(selected)}</strong>
              <span>Category</span><strong>{selected.category}</strong>
              <span>Amount</span><strong>₹{selected.amount_paid || 0}</strong>
            </div>
            <button className="btn-primary" onClick={() => setSelected(null)}>Close</button>
          </div>
        </div>
      )}
    </div>
  );
}
