import { useEffect, useState } from "react";
import { Shield, Trash2 } from "lucide-react";
import { api } from "../api";
import { Book, AdminBorrow } from "../types";

const CATEGORIES = ["Web Development", "Data Science", "AI/ML", "Cybersecurity"];

const CATEGORY_PRICES: Record<string, { download: number; rent: number }> = {
  "Web Development": { download: 29, rent: 99 },
  "Data Science": { download: 39, rent: 119 },
  "AI/ML": { download: 49, rent: 139 },
  Cybersecurity: { download: 49, rent: 149 },
};

const emptyForm = {
  title: "",
  author: "",
  category: "Web Development",
  description: "",
};

export default function AdminPage() {
  const [books, setBooks] = useState<Book[]>([]);
  const [borrows, setBorrows] = useState<AdminBorrow[]>([]);
  const [form, setForm] = useState(emptyForm);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState("");
  const [toastType, setToastType] = useState<"success" | "error">("success");

  const load = async () => {
    const [bRes, brRes] = await Promise.all([api.books(), api.adminBorrows()]);
    if (bRes.success && bRes.data) setBooks(bRes.data.books);
    if (brRes.success && brRes.data) setBorrows(brRes.data.borrows);
    setLoading(false);
  };

  useEffect(() => {
    load();
  }, []);

  const showToast = (msg: string, type: "success" | "error" = "success") => {
    setToast(msg);
    setToastType(type);
    setTimeout(() => setToast(""), 3000);
  };

  const handleUploadPdf = async (bookId: number, file: File) => {
    const res = await api.adminUploadPdf(bookId, file);
    if (res.success) {
      showToast("PDF uploaded successfully");
      await load();
    } else {
      showToast(res.error || "PDF upload failed", "error");
    }
  };

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.title.trim() || !form.author.trim()) {
      showToast("Fill in title and author", "error");
      return;
    }
    const res = await api.adminAddBook({
      title: form.title.trim(),
      author: form.author.trim(),
      category: form.category,
      image_url: "",
      description: form.description.trim(),
    });
    if (res.success) {
      showToast(`"${form.title}" added to the library`);
      setForm(emptyForm);
      await load();
    } else {
      showToast(res.error || "Failed to add book", "error");
    }
  };

  const handleDelete = async (book: Book) => {
    if (!confirm(`Delete "${book.title}"?`)) return;
    const res = await api.adminDeleteBook(book.id);
    if (res.success) {
      showToast(`"${book.title}" removed`);
      await load();
    } else {
      showToast(res.error || "Cannot delete book", "error");
    }
  };

  const fmt = (d?: string) =>
    d
      ? new Date(d).toLocaleDateString("en-IN", {
          day: "numeric",
          month: "short",
          year: "numeric",
        })
      : "—";

  return (
    <div className="page">
      {toast && <div className={`toast ${toastType}`}>{toast}</div>}

      <div className="page-header">
        <h1>
          <Shield size={22} strokeWidth={1.8} style={{ display: "inline", marginRight: 8, verticalAlign: "middle" }} />
          Admin Panel
        </h1>
        <p>Manage books and view active borrows across all users</p>
      </div>

      {loading ? (
        <div className="loading-state">
          <div className="spinner" />
          <p>Loading admin data...</p>
        </div>
      ) : (
        <>
          <section className="admin-section">
            <h2 className="admin-section-title">Add New Book</h2>
            <form className="admin-form" onSubmit={handleAdd}>
              <div className="admin-form-row">
                <div className="field">
                  <label>Title</label>
                  <input
                    value={form.title}
                    onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
                    placeholder="Book title"
                  />
                </div>
                <div className="field">
                  <label>Author</label>
                  <input
                    value={form.author}
                    onChange={(e) => setForm((f) => ({ ...f, author: e.target.value }))}
                    placeholder="Author name"
                  />
                </div>
              </div>
              <div className="admin-form-row">
                <div className="field">
                  <label>Category</label>
                  <select
                    value={form.category}
                    onChange={(e) => setForm((f) => ({ ...f, category: e.target.value }))}
                  >
                    {CATEGORIES.map((c) => (
                      <option key={c} value={c}>
                        {c}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="field">
                  <label>Pricing (auto by category)</label>
                  <p className="admin-price-hint">
                    Download &#8377;{CATEGORY_PRICES[form.category]?.download ?? "—"} · Rent &#8377;
                    {CATEGORY_PRICES[form.category]?.rent ?? "—"}
                  </p>
                </div>
              </div>
              <div className="field">
                <label>Description</label>
                <textarea
                  value={form.description}
                  onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
                  placeholder="Short description"
                  rows={3}
                />
              </div>
              <button type="submit" className="btn-primary admin-submit">
                Add Book
              </button>
            </form>
          </section>

          <section className="admin-section">
            <h2 className="admin-section-title">Catalog ({books.length} books)</h2>
            <div className="admin-books-list">
              {books.map((book) => (
                <div key={book.id} className="admin-book-row">
                  <div>
                    <strong>{book.title}</strong>
                    <span className="admin-book-meta">
                      {book.author} · {book.category} · DL &#8377;{book.download_price} · Rent &#8377;
                      {book.rent_price}
                      {book.pdf_path ? " · PDF" : ""}
                    </span>
                  </div>
                  <div className="admin-book-actions">
                    <label className="admin-upload-pdf">
                      <input
                        type="file"
                        accept=".pdf"
                        className="admin-upload-input"
                        onChange={(e) => {
                          const file = e.target.files?.[0];
                          if (file) handleUploadPdf(book.id, file);
                          e.target.value = "";
                        }}
                      />
                      Upload PDF
                    </label>
                    <button
                      type="button"
                      className="admin-delete-btn"
                      onClick={() => handleDelete(book)}
                      title="Delete book"
                    >
                      <Trash2 size={16} strokeWidth={1.8} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section className="admin-section">
            <h2 className="admin-section-title">Active Borrows ({borrows.length})</h2>
            {borrows.length === 0 ? (
              <p className="admin-empty">No books currently borrowed.</p>
            ) : (
              <div className="history-table-wrap">
                <table className="history-table admin-borrows-table">
                  <thead>
                    <tr>
                      <th>User</th>
                      <th>Book</th>
                      <th>Category</th>
                      <th>Borrowed</th>
                      <th>Due</th>
                    </tr>
                  </thead>
                  <tbody>
                    {borrows.map((b) => (
                      <tr key={b.id}>
                        <td>
                          <div className="admin-user-cell">
                            <strong>{b.user_name}</strong>
                            <span>{b.user_email}</span>
                          </div>
                        </td>
                        <td>
                          <strong>{b.title}</strong>
                          <div className="history-author">{b.author}</div>
                        </td>
                        <td>
                          <span className="cat-badge">{b.category}</span>
                        </td>
                        <td className="history-date">{fmt(b.borrowed_at)}</td>
                        <td className="history-date">{fmt(b.due_date)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </>
      )}
    </div>
  );
}
