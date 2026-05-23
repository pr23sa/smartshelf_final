import { useEffect, useState } from "react";
import { X } from "lucide-react";
import { Book, ReservationConfirm } from "../types";
import { API_BASE_URL, api } from "../api";
import { useAuth } from "../AuthContext";

interface BookCardProps {
  book: Book;
  onBorrow?: (book: Book) => void;
  onReturn?: (book: Book) => void;
  isBorrowed?: boolean;
  showReturn?: boolean;
  daysOverdue?: number;
  dueDate?: string;
  onToast?: (msg: string, type?: "success" | "error") => void;
  actionMode?: "browse" | "borrowed";
}

type PayMode = "download" | "reserve" | null;

function fmtDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

export default function BookCard({
  book,
  onBorrow,
  onReturn,
  isBorrowed = false,
  showReturn = false,
  daysOverdue,
  dueDate,
  onToast,
  actionMode = "browse",
}: BookCardProps) {
  const { user } = useAuth();
  const [readOpen, setReadOpen] = useState(false);
  const [payMode, setPayMode] = useState<PayMode>(null);
  const [showActions, setShowActions] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [confirm, setConfirm] = useState<ReservationConfirm | null>(null);
  const hasPdf = book.pdf_path != null && book.pdf_path !== "";

  const pdfUrl = `${API_BASE_URL}/book-pdf/${book.id}`;

  useEffect(() => {
    const handleClickOutside = () => setShowActions(false);
    if (showActions) {
      document.addEventListener("click", handleClickOutside);
    }
    return () => document.removeEventListener("click", handleClickOutside);
  }, [showActions]);

  const handleDownloadPay = async () => {
    if (!user) {
      onToast?.("Please log in to download this book.", "error");
      setPayMode(null);
      return;
    }
    if (!hasPdf) {
      onToast?.("PDF not available for this book yet.", "error");
      setPayMode(null);
      return;
    }
    setProcessing(true);
    await new Promise((r) => setTimeout(r, 1500));
    const res = await api.recordDownloadPayment(book.id, user.id, book.download_price);
    setPayMode(null);
    setProcessing(false);
    if (!res.success) {
      onToast?.(res.error || "Payment failed", "error");
      return;
    }
    const link = document.createElement("a");
    link.href = pdfUrl;
    link.download = `${book.title.replace(/[^a-zA-Z0-9\s]/g, "").replace(/\s+/g, "_")}.pdf`;
    link.target = "_blank";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    onToast?.("Payment successful! Added to My Books and download started.", "success");
  };

  const handleReservePay = async () => {
    if (!user) return;
    setProcessing(true);
    await new Promise((r) => setTimeout(r, 1500));
    const res = await api.reserve(book.id, user.id, book.rent_price);
    setPayMode(null);
    setProcessing(false);
    if (res.success && res.data) {
      setConfirm(res.data.reservation);
    } else {
      onToast?.(res.error || "Reservation failed", "error");
    }
  };

  return (
    <>
      <div className="book-card">
        <div className="book-info">
          <span className="book-category">{book.category}</span>
          <h3 className="book-title">{book.title}</h3>
          <p className="book-author">{book.author}</p>
          {dueDate && showReturn && <p className="book-due-date">Due: {fmtDate(dueDate)}</p>}

          {actionMode === "browse" ? (
            <>
              <div className="book-actions">
                {hasPdf && (
                  <button type="button" className="btn-card-action btn-card-read" onClick={() => setReadOpen(true)}>
                    Read Free
                  </button>
                )}
                <button type="button" className="btn-card-action btn-card-download" onClick={() => setPayMode("download")}>
                  Download &#8377;{book.download_price}
                </button>
                <button type="button" className="btn-card-action btn-card-reserve" onClick={() => setPayMode("reserve")}>
                  Reserve Hard Copy &#8377;{book.rent_price}
                </button>
              </div>
              <div className="mobile-actions-wrap" style={{ position: "relative" }}>
                <button
                  className="three-dot-btn"
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    setShowActions(!showActions);
                  }}
                >
                  ···
                </button>
                {showActions && (
                  <div className="actions-dropdown">
                    {hasPdf && (
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          setReadOpen(true);
                          setShowActions(false);
                        }}
                      >
                        Read Free
                      </button>
                    )}
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        setPayMode("download");
                        setShowActions(false);
                      }}
                    >
                      Download &#8377;{book.download_price}
                    </button>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        setPayMode("reserve");
                        setShowActions(false);
                      }}
                    >
                      Reserve Hard Copy &#8377;{book.rent_price}
                    </button>
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="book-footer">
              <span className="book-price">&#8377;{book.rent_price} rent</span>
              {showReturn && isBorrowed ? (
                <button type="button" className="btn-return" onClick={() => onReturn?.(book)}>
                  Return Book
                </button>
              ) : (
                <button
                  type="button"
                  className="btn-borrow"
                  disabled={!book.available || isBorrowed}
                  onClick={() => onBorrow?.(book)}
                >
                  {isBorrowed ? "Borrowed" : book.available ? "Borrow" : "Unavailable"}
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      {readOpen && hasPdf && (
        <div
          className="pdf-reader-overlay"
          style={{ padding: 0, alignItems: "flex-start" }}
          onClick={() => setReadOpen(false)}
        >
          <div
            className="pdf-reader-modal"
            style={{
              width: "100vw",
              height: "100vh",
              maxWidth: "100vw",
              maxHeight: "100vh",
              borderRadius: 0,
              margin: 0,
              padding: 0,
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <button type="button" className="pdf-reader-close" onClick={() => setReadOpen(false)} aria-label="Close">
              <X size={22} />
            </button>
            <h3 className="pdf-reader-title">{book.title}</h3>
            <iframe
              src={`${pdfUrl}#toolbar=0&navpanes=0&scrollbar=1`}
              title={book.title}
              className="pdf-reader-frame"
            />
          </div>
        </div>
      )}

      {payMode && !processing && (
        <div className="payment-overlay" onClick={() => setPayMode(null)}>
          <div className="pay-modal" onClick={(e) => e.stopPropagation()}>
            <button type="button" className="pay-modal-close" onClick={() => setPayMode(null)} aria-label="Close">
              <X size={20} />
            </button>

            <div className="pay-modal-header">
              <h3>{book.title}</h3>
              <p className="pay-modal-author">by {book.author}</p>
            </div>

            <div className="pay-modal-amount-box">
              <span className="pay-amount-label">Amount to Pay</span>
              <span className="pay-amount-value">
                &#8377;{payMode === "download" ? book.download_price : book.rent_price}
              </span>
              {payMode === "reserve" && (
                <span className="pay-amount-note">30-day hard copy rental</span>
              )}
            </div>

            <div className="pay-demo-notice">
              <span>{"\uD83D\uDD12"}</span>
              <p>Demo Payment &mdash; No real money charged</p>
            </div>

            <button
              type="button"
              className="btn-pay-submit"
              onClick={payMode === "download" ? handleDownloadPay : handleReservePay}
              disabled={processing}
            >
              {processing ? "Processing..." : `Confirm & Pay \u20B9${payMode === "download" ? book.download_price : book.rent_price}`}
            </button>
          </div>
        </div>
      )}

      {processing && (
        <div className="payment-overlay">
          <div className="payment-modal">
            <div className="payment-spinner" />
            <p>Processing payment...</p>
          </div>
        </div>
      )}

      {confirm && (
        <div className="payment-overlay">
          <div className="reservation-confirm-modal">
            <h2 className="reservation-confirm-title">Reservation Confirmed!</h2>
            <div className="reservation-confirm-book">
              <div>
                <h3>{confirm.title}</h3>
                <p>by {confirm.author}</p>
              </div>
            </div>
            <div className="reservation-confirm-details">
              <p>
                <span>Student</span> {confirm.user_name}
              </p>
              <p>
                <span>Email</span> {confirm.user_email}
              </p>
              <p>
                <span>Reserved on</span> {fmtDate(confirm.reservation_date)}
              </p>
              <p>
                <span>Pickup by</span> {confirm.pickup_deadline ? fmtDate(confirm.pickup_deadline) : "Within 24 hours"}
              </p>
              <p>
                <span>Reservation ID</span> <code>{confirm.reservation_id}</code>
              </p>
              <p>
                <span>Amount paid</span> &#8377;{confirm.amount_paid}
              </p>
            </div>
            <p className="reservation-pickup-note">
              Pick up your book within 24 hours. Visit the library with this Reservation ID.
            </p>
            <button type="button" className="btn-primary" onClick={() => setConfirm(null)}>
              Close
            </button>
          </div>
        </div>
      )}
    </>
  );
}
