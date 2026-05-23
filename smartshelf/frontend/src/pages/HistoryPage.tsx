import { useEffect, useMemo, useState } from "react";
import { API_BASE_URL } from "../api";
import { useAuth } from "../AuthContext";
import EmptyState from "../components/EmptyState";

type BorrowHistoryRecord = {
  id: number;
  book_id: number;
  title: string;
  author: string;
  category: string;
  borrow_type: string;
  status: string;
  borrow_date: string | null;
  reserved_date: string | null;
  pickup_deadline: string | null;
  due_date: string | null;
  return_date: string | null;
  amount_paid: number;
  reservation_id?: string | null;
  days_overdue: number;
  days_remaining: number | null;
  display_status?: string;
  reservedAt?: string | null;
  pickedUpAt?: string | null;
  dueDate?: string | null;
  returnedAt?: string | null;
  is_overdue: boolean;
};

type FilterKey = "all" | "digital" | "hard-copy" | "reserved" | "returned";

const FILTERS: { key: FilterKey; label: string }[] = [
  { key: "all", label: "All" },
  { key: "digital", label: "Digital" },
  { key: "hard-copy", label: "Hard Copy" },
  { key: "reserved", label: "Reserved" },
  { key: "returned", label: "Returned" },
];

function fmtDate(date?: string | null) {
  if (!date) return "N/A";
  return new Date(date).toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

function fmtShortDate(date?: string | null) {
  if (!date) return "N/A";
  return new Date(date).toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
  });
}

function transactionType(record: BorrowHistoryRecord) {
  if (record.status === "returned") return "Returned";
  if (record.status === "reserved") return "Reserved";
  if (record.borrow_type === "digital" || record.status === "owned") return "Downloaded";
  if (record.status === "borrowed") return "Borrowed";
  return "Borrowed";
}

function activityDate(record: BorrowHistoryRecord) {
  return record.return_date || record.borrow_date || record.reserved_date || record.due_date;
}

function matchesFilter(record: BorrowHistoryRecord, filter: FilterKey) {
  if (filter === "all") return true;
  if (filter === "digital") return record.borrow_type === "digital" || record.status === "owned";
  if (filter === "hard-copy") return record.borrow_type === "hard copy";
  if (filter === "reserved") return record.status === "reserved";
  return record.status === "returned";
}

function statusTone(record: BorrowHistoryRecord) {
  if (record.status === "returned" || record.status === "owned" || record.borrow_type === "digital") return "success";
  return "info";
}

function MetadataItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col" style={{ display: "flex", flexDirection: "column", minWidth: 0 }}>
      <span style={{ color: "#64748B", fontSize: 13, fontWeight: 600, lineHeight: 1.35 }}>{label}</span>
      <span style={{ color: "#111827", fontSize: 15, fontWeight: 700, lineHeight: 1.45 }}>
        {value}
      </span>
    </div>
  );
}

type HistoryCardProps = {
  record: BorrowHistoryRecord;
  isOpen: boolean;
  onToggle: () => void;
};

function HistoryCard({ record, isOpen, onToggle }: HistoryCardProps) {
  const isDigital = record.borrow_type === "digital" || record.status === "owned";
  const status = transactionType(record);
  const borrowedDate = record.pickedUpAt || record.borrow_date;
  const returnedDate = record.returnedAt || record.return_date;
  const isHardCopy = record.borrow_type === "hard copy";
  const metadataRows = isHardCopy ? [
    ["Reserved", fmtShortDate(record.reserved_date)],
    [record.status === "reserved" ? "Pending" : "Picked Up", fmtShortDate(borrowedDate)],
    ["Due", fmtShortDate(record.dueDate || record.due_date)],
    ["Reservation ID", record.reservation_id || (record.status === "reserved" ? `RES-${record.id}` : "N/A")],
    ["Borrowed Date", fmtDate(borrowedDate)],
    ["Returned Date", fmtDate(returnedDate)],
  ] : [
    ["Reservation ID", record.reservation_id || "N/A"],
    [isDigital ? "Downloaded Date" : "Borrowed Date", fmtDate(isDigital ? activityDate(record) : borrowedDate)],
    ["Returned Date", fmtDate(returnedDate)],
  ];

  return (
    <article className={`history-feed-card ${isOpen ? "open" : ""}`} key={record.id}>
      <button
        className="history-feed-summary"
        onClick={onToggle}
        style={{ alignItems: "start", gap: 24, padding: "14px 16px" }}
      >
        <span className="history-summary-main">
          <strong style={{ fontSize: 17, lineHeight: 1.3 }}>{record.title}</strong>
          <small style={{ fontSize: 13, lineHeight: 1.45 }}>{record.author}</small>
        </span>
        <span className="history-summary-meta" style={{ alignItems: "flex-end", gap: 6, paddingTop: 2 }}>
          <span
            className={`library-chip ${statusTone(record)}`}
            style={{ minHeight: 24, padding: "4px 10px", fontSize: 11 }}
          >
            {status}
          </span>
          <small style={{ fontSize: 13, lineHeight: 1.4, whiteSpace: "nowrap" }}>{fmtDate(activityDate(record))}</small>
        </span>
      </button>

      {isOpen && (
        <div
          className="grid grid-cols-3 gap-x-16 gap-y-8"
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(3, minmax(0, 1fr))",
            columnGap: 64,
            rowGap: 32,
            padding: "2px 16px 16px",
            alignItems: "start",
          }}
        >
          {metadataRows.map(([label, value]) => (
            <MetadataItem key={label} label={label} value={value} />
          ))}
        </div>
      )}
    </article>
  );
}

interface HistoryPageProps {
  setPage: (p: string) => void;
}

export default function HistoryPage({ setPage }: HistoryPageProps) {
  const { user } = useAuth();
  const [history, setHistory] = useState<BorrowHistoryRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<FilterKey>("all");
  const [query, setQuery] = useState("");
  const [openId, setOpenId] = useState<number | null>(null);

  useEffect(() => {
    if (!user) return;
    const loadHistory = async () => {
      setLoading(true);
      try {
        const res = await fetch(`${API_BASE_URL}/api/borrowed/${user.id}`);
        const data = await res.json();
        setHistory(data.success ? data.borrows || [] : []);
      } catch {
        setHistory([]);
      }
      setLoading(false);
    };

    loadHistory();
  }, [user]);

  const stats = useMemo(() => {
    const activeBorrows = history.filter((h) => h.status === "borrowed").length;
    const digitalOwned = history.filter((h) => h.borrow_type === "digital" || h.status === "owned").length;
    const pendingReturns = history.filter((h) => h.status === "borrowed" && h.borrow_type === "hard copy").length;
    return { total: history.length, activeBorrows, digitalOwned, pendingReturns };
  }, [history]);

  const hasStats = stats.total > 0
    || stats.activeBorrows > 0
    || stats.digitalOwned > 0
    || stats.pendingReturns > 0;

  const filtered = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    return history.filter((record) => {
      const searchHit = !normalized
        || record.title.toLowerCase().includes(normalized)
        || record.author.toLowerCase().includes(normalized)
        || record.category.toLowerCase().includes(normalized)
        || String(record.reservation_id || record.id).toLowerCase().includes(normalized);
      return searchHit && matchesFilter(record, filter);
    });
  }, [history, filter, query]);

  return (
    <div className="page history-page-shell">
      <div className="page-header">
        <h1>Transaction History</h1>
        <p>Detailed activity for reservations, downloads, returns, and payments.</p>
      </div>

      {hasStats && (
        <>
          <div className="library-stats-grid">
            <div className="library-stat-card"><span>Total Books</span><strong>{stats.total}</strong></div>
            <div className="library-stat-card"><span>Active Borrows</span><strong>{stats.activeBorrows}</strong></div>
            <div className="library-stat-card"><span>Digital Owned</span><strong>{stats.digitalOwned}</strong></div>
            <div className="library-stat-card"><span>Pending Returns</span><strong>{stats.pendingReturns}</strong></div>
          </div>

          <div className="history-controls">
            <div className="history-search">
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search title, author, category, reservation ID"
              />
            </div>
            <div className="history-filter-tabs">
              {FILTERS.map((item) => (
                <button
                  key={item.key}
                  className={filter === item.key ? "active" : ""}
                  onClick={() => setFilter(item.key)}
                >
                  {item.label}
                </button>
              ))}
            </div>
          </div>
        </>
      )}

      {loading && (
        <div className="history-feed">
          {[1, 2, 3].map((item) => <div className="history-skeleton-row" key={item} />)}
        </div>
      )}

      {!loading && history.length === 0 && (
        <EmptyState
          title="No reading activity yet"
          subtitle="Browse books and track your reading history here."
          action={{ label: "Browse Books", onClick: () => setPage("books") }}
          meta={[
            { value: "80+", label: "Books Available" },
            { value: "24h", label: "Reservation Pickup" },
            { value: "PDF", label: "Digital Reading" },
          ]}
          guidance={["Borrow books", "Read or reserve", "Track activity"]}
        />
      )}

      {!loading && history.length > 0 && filtered.length === 0 && (
        <div className="library-empty-state">
          <h3>No matching transactions</h3>
          <p>Try a different search or filter.</p>
        </div>
      )}

      {!loading && filtered.length > 0 && (
        <div className="history-feed">
          {filtered.map((record) => {
            const isOpen = openId === record.id;
            return <HistoryCard key={record.id} record={record} isOpen={isOpen} onToggle={() => setOpenId(isOpen ? null : record.id)} />;
          })}
        </div>
      )}
    </div>
  );
}
