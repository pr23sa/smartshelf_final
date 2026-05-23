from flask import Flask, request, jsonify, g, send_file
import hashlib
import os
import secrets
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from functools import wraps
from werkzeug.utils import secure_filename
from recommendations import get_recommendations
from database import init_db, get_db, migrate_schema, seed_admin

app = Flask(__name__)
@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})

def migrate_borrows_table():
    conn = get_db()
    cur = conn.cursor()
    columns_to_add = [
        ("borrow_type", "TEXT DEFAULT 'hard copy'"),
        ("status", "TEXT DEFAULT 'borrowed'"),
        ("reserved_date", "TEXT"),
        ("pickup_deadline", "TEXT"),
        ("return_date", "TEXT"),
        ("amount_paid", "REAL DEFAULT 0"),
    ]
    for col, definition in columns_to_add:
        try:
            cur.execute(f"ALTER TABLE borrows ADD COLUMN {col} {definition}")
            conn.commit()
        except Exception:
            pass
    conn.close()

JWT_SECRET = os.environ.get("JWT_SECRET", "smartshelf-dev-secret-change-in-production")
JWT_ALGORITHM = "HS256"
BORROW_DAYS = 30
RESERVE_DAYS = 30

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_DIR = os.path.join(BASE_DIR, "uploads", "pdfs")
os.makedirs(PDF_DIR, exist_ok=True)

CATEGORY_PRICES = {
    "Web Development": (29, 99),
    "Data Science": (39, 119),
    "AI/ML": (49, 139),
    "Cybersecurity": (49, 149),
}

@app.after_request
def add_cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
    return response

@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        from flask import Response
        res = Response()
        res.headers["Access-Control-Allow-Origin"] = "*"
        res.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
        res.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
        return res

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(password: str, stored: str) -> bool:
    if stored.startswith("$2"):
        return bcrypt.checkpw(password.encode("utf-8"), stored.encode("utf-8"))
    return hashlib.sha256(password.encode()).hexdigest() == stored

def create_token(user_id: int) -> str:
    return jwt.encode({"sub": str(user_id)}, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

def user_row_to_dict(row) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "email": row["email"],
        "is_admin": bool(row["is_admin"]) if "is_admin" in row.keys() else False,
    }

def success(data):
    return jsonify({"success": True, "data": data})

def error(msg, code=400):
    return jsonify({"success": False, "error": msg}), code

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return error("Unauthorized — missing token", 401)
        try:
            payload = decode_token(auth[7:])
            g.user_id = int(payload["sub"])
        except jwt.ExpiredSignatureError:
            return error("Token expired", 401)
        except jwt.InvalidTokenError:
            return error("Invalid token", 401)
        return f(*args, **kwargs)
    return decorated

def require_admin(f):
    @wraps(f)
    @require_auth
    def decorated(*args, **kwargs):
        db = get_db()
        user = db.execute(
            "SELECT is_admin FROM users WHERE id = ?", (g.user_id,)
        ).fetchone()
        if not user or not user["is_admin"]:
            return error("Admin access required", 403)
        return f(*args, **kwargs)
    return decorated


def utc_now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def ensure_borrow_tracking_columns(db):
    cols = {row[1] for row in db.execute("PRAGMA table_info(transactions)").fetchall()}
    if "borrow_type" not in cols:
        db.execute("ALTER TABLE transactions ADD COLUMN borrow_type TEXT DEFAULT 'hard copy'")
    if "pickup_deadline" not in cols:
        db.execute("ALTER TABLE transactions ADD COLUMN pickup_deadline TEXT")
    if "reserved_date" not in cols:
        db.execute("ALTER TABLE transactions ADD COLUMN reserved_date TEXT")

def ensure_borrows_table():
    import sqlite3
    conn = sqlite3.connect("smartshelf.db")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS borrows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            book_id INTEGER NOT NULL,
            borrow_date TEXT,
            due_date TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (book_id) REFERENCES books(id)
        )
    """)
    columns_to_add = [
        ("borrow_type", "TEXT DEFAULT 'hard copy'"),
        ("status", "TEXT DEFAULT 'borrowed'"),
        ("reserved_date", "TEXT"),
        ("pickup_deadline", "TEXT"),
        ("return_date", "TEXT"),
        ("amount_paid", "REAL DEFAULT 0"),
    ]
    for col, definition in columns_to_add:
        try:
            cur.execute(f"ALTER TABLE borrows ADD COLUMN {col} {definition}")
        except sqlite3.OperationalError:
            pass
    conn.commit()
    conn.close()

def backfill_borrows_from_reservations():
    db = get_db()
    ensure_borrows_table()
    db.execute("""
        INSERT INTO borrows
            (user_id, book_id, borrow_date, reserved_date, pickup_deadline, due_date, status, borrow_type, amount_paid)
        SELECT
            r.user_id,
            r.book_id,
            NULL,
            r.reservation_date,
            datetime(r.reservation_date, '+24 hours'),
            NULL,
            'reserved',
            'hard copy',
            r.amount_paid
        FROM reservations r
        WHERE NOT EXISTS (
            SELECT 1
            FROM borrows b
            WHERE b.user_id = r.user_id
              AND b.book_id = r.book_id
              AND b.reserved_date = r.reservation_date
              AND b.status = 'reserved'
        )
    """)
    db.commit()
    db.close()

ensure_borrows_table()
migrate_borrows_table()
backfill_borrows_from_reservations()

# ─── AUTH ───────────────────────────────────────────────────────────────────

@app.route("/signup", methods=["POST"])
def signup():
    body = request.get_json() or {}
    name = body.get("name", "").strip()
    email = body.get("email", "").strip().lower()
    password = body.get("password", "")

    if not name or not email or not password:
        return error("All fields are required")

    db = get_db()
    existing = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    if existing:
        return error("Email already registered")

    hashed = hash_password(password)
    db.execute(
        "INSERT INTO users (name, email, password, is_admin) VALUES (?, ?, ?, 0)",
        (name, email, hashed),
    )
    db.commit()

    user = db.execute(
        "SELECT id, name, email, is_admin FROM users WHERE email = ?", (email,)
    ).fetchone()
    user_dict = user_row_to_dict(user)
    token = create_token(user_dict["id"])
    return success({"user": user_dict, "token": token}), 201

@app.route("/login", methods=["POST"])
def login():
    body = request.get_json() or {}
    email = body.get("email", "").strip().lower()
    password = body.get("password", "")

    db = get_db()
    user = db.execute(
        "SELECT id, name, email, password, is_admin FROM users WHERE email = ?",
        (email,),
    ).fetchone()

    if not user or not verify_password(password, user["password"]):
        return error("Invalid email or password", 401)

    if not user["password"].startswith("$2"):
        db.execute(
            "UPDATE users SET password = ? WHERE id = ?",
            (hash_password(password), user["id"]),
        )
        db.commit()

    user_dict = user_row_to_dict(user)
    token = create_token(user_dict["id"])
    return success({"user": user_dict, "token": token})

# ─── BOOKS ──────────────────────────────────────────────────────────────────

@app.route("/books", methods=["GET"])
def list_books():
    db = get_db()
    books = db.execute("SELECT * FROM books ORDER BY id").fetchall()
    return success({"books": [dict(b) for b in books]})

@app.route("/book-pdf/<int:book_id>", methods=["GET"])
def serve_book_pdf(book_id):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(base_dir, "uploads", "pdfs", f"book_{book_id}.pdf")
    if not os.path.isfile(filepath):
        return error("PDF not available for this book", 404)
    response = send_file(
        filepath,
        mimetype="application/pdf",
        as_attachment=False,
        download_name=f"book_{book_id}.pdf",
    )
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    return response

# ─── RESERVATIONS (HARD COPY) ─────────────────────────────────────────────────

@app.route("/api/download-payment", methods=["POST"])
@require_auth
def record_download_payment():
    body = request.get_json() or {}
    book_id = body.get("book_id")
    amount = body.get("amount")
    req_user_id = body.get("user_id")

    if req_user_id is not None and int(req_user_id) != g.user_id:
        return error("Forbidden", 403)
    if not book_id:
        return error("book_id is required")

    db = get_db()
    book = db.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
    if not book:
        return error("Book not found", 404)

    download_price = book["download_price"]
    if amount is not None and int(amount) != download_price:
        return error(f"Invalid amount. Expected {download_price}", 400)

    ensure_borrows_table()
    user_id = g.user_id
    existing = db.execute(
        """SELECT id FROM borrows
           WHERE user_id = ? AND book_id = ? AND status = 'owned' AND borrow_type = 'digital'
           ORDER BY id DESC LIMIT 1""",
        (user_id, book_id),
    ).fetchone()
    if existing:
        return success({"message": "Download already owned", "borrow_id": existing["id"]})

    print(f"DEBUG: Inserting borrow record - user_id={user_id}, book_id={book_id}, type=digital")
    cur = db.execute(
        """INSERT INTO borrows
           (user_id, book_id, borrow_date, due_date, reserved_date, pickup_deadline, return_date, status, borrow_type, amount_paid)
           VALUES (?, ?, datetime('now'), NULL, NULL, NULL, NULL, 'owned', 'digital', ?)""",
        (user_id, book_id, download_price),
    )
    print(f"DEBUG: Insert successful, rows affected={cur.rowcount}")
    db.commit()
    print(f"DEBUG: Committed successfully")
    return success({"message": "Download payment recorded", "borrow_id": cur.lastrowid})

@app.route("/api/send-otp", methods=["POST"])
def send_otp():
    data = request.get_json() or {}
    email = data.get("email")
    if not email:
        return jsonify({"error": "Email required"}), 400

    import random
    otp = str(random.randint(100000, 999999))

    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    sender_email = "your_gmail@gmail.com"  # TODO: Replace with real Gmail address.
    sender_password = "your_app_password"  # TODO: Replace with Gmail App Password.

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = email
    msg["Subject"] = "SmartShelf Payment OTP"

    body = f"""
    Hello,

    Your SmartShelf payment verification OTP is:

    {otp}

    This OTP is valid for 5 minutes.
    Do not share this with anyone.

    - SmartShelf AI Library
    """
    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, email, msg.as_string())
        server.quit()
        return jsonify({"success": True, "otp": otp})
    except Exception as e:
        print(f"Email error: {e}")
        return jsonify({"success": False, "otp": otp, "note": "Email failed but OTP returned for demo"})

def _generate_reservation_id():
    return f"RES-{secrets.token_hex(4).upper()}"

@app.route("/reserve", methods=["POST"])
@require_auth
def reserve_hard_copy():
    body = request.get_json() or {}
    book_id = body.get("book_id")
    amount = body.get("amount")
    req_user_id = body.get("user_id")

    if req_user_id is not None and int(req_user_id) != g.user_id:
        return error("Forbidden", 403)

    if not book_id or amount is None:
        return error("book_id and amount are required")

    try:
        book_id = int(book_id)
        amount = int(amount)
    except (TypeError, ValueError):
        return error("book_id and amount must be numbers")

    db = get_db()
    book = db.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
    if not book:
        return error("Book not found", 404)

    if amount != book["rent_price"]:
        return error(f"Invalid amount. Expected ₹{book['rent_price']}", 400)

    now = utc_now_iso()
    pickup_deadline = (datetime.now(timezone.utc) + timedelta(hours=24)).replace(microsecond=0).isoformat()
    due = None
    reservation_due_value = pickup_deadline
    reservation_id = _generate_reservation_id()
    ensure_borrow_tracking_columns(db)

    cur = db.execute(
        """INSERT INTO reservations
           (user_id, book_id, reservation_id, status, reservation_date, due_date, amount_paid)
           VALUES (?, ?, ?, 'reserved', ?, ?, ?)""",
        (g.user_id, book_id, reservation_id, now, reservation_due_value, amount),
    )
    db.execute(
        """INSERT INTO transactions
           (user_id, book_id, status, date, borrowed_at, due_date, borrow_type, reserved_date, pickup_deadline)
           VALUES (?, ?, 'reserved', ?, NULL, ?, 'hard copy', ?, ?)""",
        (g.user_id, book_id, now, due, now, pickup_deadline),
    )
    ensure_borrows_table()
    user_id = g.user_id
    borrow_type = "hard copy"
    print(f"DEBUG: Inserting borrow record - user_id={user_id}, book_id={book_id}, type={borrow_type}")
    borrow_cur = db.execute(
        """INSERT INTO borrows
           (user_id, book_id, borrow_date, reserved_date, pickup_deadline, due_date, status, borrow_type, amount_paid)
           VALUES (?, ?, NULL, datetime('now'), datetime('now', '+24 hours'), NULL, 'reserved', 'hard copy', ?)""",
        (user_id, book_id, amount),
    )
    print(f"DEBUG: Insert successful, rows affected={borrow_cur.rowcount}")
    db.commit()
    print(f"DEBUG: Committed successfully")

    user = db.execute(
        "SELECT name, email FROM users WHERE id = ?", (g.user_id,)
    ).fetchone()

    return success({
        "reservation": {
            "id": cur.lastrowid,
            "reservation_id": reservation_id,
            "book_id": book_id,
            "title": book["title"],
            "author": book["author"],
            "image_url": book["image_url"],
            "category": book["category"],
            "user_name": user["name"],
            "user_email": user["email"],
            "reservation_date": now,
            "pickup_deadline": pickup_deadline,
            "due_date": due,
            "amount_paid": amount,
            "status": "reserved",
        }
    }), 201

@app.route("/reservations/<int:user_id>", methods=["GET"])
@require_auth
def list_reservations(user_id):
    if user_id != g.user_id:
        return error("Forbidden", 403)

    db = get_db()
    rows = db.execute("""
        SELECT r.*, b.title, b.author, b.image_url, b.category
        FROM reservations r
        JOIN books b ON r.book_id = b.id
        WHERE r.user_id = ?
        ORDER BY r.reservation_date DESC
    """, (user_id,)).fetchall()

    return success({"reservations": [dict(r) for r in rows]})

# ─── BORROW / RETURN ──────────────────────────────────────────────────────────

@app.route("/borrow", methods=["POST"])
@require_auth
def borrow():
    body = request.get_json() or {}
    book_id = body.get("book_id")

    if not book_id:
        return error("book_id is required")

    db = get_db()
    user_id = g.user_id
    book = db.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
    if not book:
        return error("Book not found", 404)
    if not book["available"]:
        return error("Book is not available")

    active = db.execute(
        "SELECT id FROM transactions WHERE user_id = ? AND book_id = ? AND status = 'borrowed'",
        (user_id, book_id),
    ).fetchone()
    if active:
        return error("You have already borrowed this book")

    now = utc_now_iso()
    due = (datetime.now(timezone.utc) + timedelta(days=BORROW_DAYS)).replace(microsecond=0).isoformat()
    ensure_borrow_tracking_columns(db)

    db.execute(
        """INSERT INTO transactions (user_id, book_id, status, date, borrowed_at, due_date, borrow_type)
           VALUES (?, ?, 'borrowed', ?, ?, ?, 'hard copy')""",
        (user_id, book_id, now, now, due),
    )
    ensure_borrows_table()
    borrow_type = "hard copy"
    print(f"DEBUG: Inserting borrow record - user_id={user_id}, book_id={book_id}, type={borrow_type}")
    borrow_cur = db.execute(
        """INSERT INTO borrows (user_id, book_id, borrow_date, due_date, status, borrow_type, amount_paid)
           VALUES (?, ?, datetime('now'), ?, 'borrowed', 'hard copy', ?)""",
        (user_id, book_id, due, book["rent_price"]),
    )
    print(f"DEBUG: Insert successful, rows affected={borrow_cur.rowcount}")
    db.execute("UPDATE books SET available = 0 WHERE id = ?", (book_id,))
    db.commit()
    print(f"DEBUG: Committed successfully")

    return success({"message": "Book borrowed successfully", "due_date": due})

@app.route("/return", methods=["POST"])
@require_auth
def return_transaction_book():
    body = request.get_json() or {}
    book_id = body.get("book_id")

    if not book_id:
        return error("book_id is required")

    db = get_db()
    user_id = g.user_id
    tx = db.execute(
        "SELECT id FROM transactions WHERE user_id = ? AND book_id = ? AND status = 'borrowed'",
        (user_id, book_id),
    ).fetchone()

    if not tx:
        return error("No active borrow record found")

    now = utc_now_iso()
    db.execute(
        "UPDATE transactions SET status = 'returned', date = ? WHERE id = ?",
        (now, tx["id"]),
    )
    db.execute("UPDATE books SET available = 1 WHERE id = ?", (book_id,))
    db.commit()

    return success({"message": "Book returned successfully"})

# ─── HISTORY / OVERDUE ────────────────────────────────────────────────────────

def _parse_db_datetime(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)

@app.route("/api/borrowed/<int:user_id>", methods=["GET"])
def get_borrowed(user_id):
    try:
        conn = get_db()
        cur = conn.cursor()
        print(f"DEBUG: Fetching borrows for user_id={user_id}")
        cur.execute("""
            SELECT
                b.id,
                b.user_id,
                b.book_id,
                bk.title,
                bk.author,
                bk.category,
                bk.image_url,
                bk.pdf_path,
                (
                    SELECT r.reservation_id
                    FROM reservations r
                    WHERE r.user_id = b.user_id
                      AND r.book_id = b.book_id
                      AND r.status IN ('reserved', 'picked_up', 'returned')
                    ORDER BY r.id DESC
                    LIMIT 1
                ) as reservation_id,
                COALESCE(b.borrow_type, 'hard copy') as borrow_type,
                COALESCE(b.status, 'borrowed') as status,
                b.borrow_date,
                b.due_date,
                b.reserved_date,
                b.pickup_deadline,
                b.return_date,
                COALESCE(b.amount_paid, 0) as amount_paid
            FROM borrows b
            JOIN books bk ON b.book_id = bk.id
            WHERE b.user_id = ?
            ORDER BY b.id DESC
        """, (user_id,))
        rows = cur.fetchall()
        print(f"DEBUG: Found {len(rows)} borrow records")
        conn.close()

        from datetime import datetime
        now = datetime.now()
        result = []
        for row in rows:
            record = {
                'id': row[0],
                'user_id': row[1],
                'book_id': row[2],
                'title': row[3],
                'author': row[4],
                'category': row[5],
                'image_url': row[6],
                'pdf_path': row[7],
                'reservation_id': row[8],
                'borrow_type': row[9],
                'status': row[10],
                'borrow_date': row[11],
                'due_date': row[12],
                'reserved_date': row[13],
                'pickup_deadline': row[14],
                'return_date': row[15],
                'amount_paid': row[16],
            }

            # Calculate overdue
            days_overdue = 0
            days_remaining = None
            is_overdue = False
            if record['due_date'] and record['status'] == 'borrowed':
                try:
                    due = _parse_db_datetime(record['due_date'])
                    if now > due:
                        overdue_seconds = (now - due).total_seconds()
                        days_overdue = max(1, int((overdue_seconds + 86399) // 86400))
                        is_overdue = True
                    else:
                        remaining_seconds = (due - now).total_seconds()
                        days_remaining = max(0, int((remaining_seconds + 86399) // 86400))
                except:
                    pass
            record['days_overdue'] = days_overdue
            record['days_remaining'] = days_remaining
            record['is_overdue'] = is_overdue
            record['display_status'] = 'overdue' if is_overdue else record['status']
            record['reservedAt'] = record['reserved_date']
            record['pickedUpAt'] = record['borrow_date'] if record['status'] in ('borrowed', 'returned') else None
            record['dueDate'] = record['due_date']
            record['returnedAt'] = record['return_date']

            # Calculate pickup countdown
            hours_until_pickup = None
            if record['pickup_deadline'] and record['status'] == 'reserved':
                try:
                    deadline = _parse_db_datetime(record['pickup_deadline'])
                    diff = (deadline - now).total_seconds() / 3600
                    hours_until_pickup = round(diff, 1)
                except:
                    pass
            record['hours_until_pickup'] = hours_until_pickup

            result.append(record)

        print(f"DEBUG: Returning {len(result)} records")
        return jsonify({"success": True, "borrows": result})

    except Exception as e:
        import traceback
        print(f"ERROR in get_borrowed: {traceback.format_exc()}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/borrowed", methods=["GET"])
@require_auth
def borrowed_books():
    return get_borrowed(g.user_id)

@app.route("/api/pickup", methods=["POST"])
def pickup_book():
    try:
        data = request.get_json() or {}
        borrow_id = data.get("borrow_id")
        user_id = data.get("user_id")
        book_id = data.get("book_id")

        if not borrow_id or not user_id or not book_id:
            return jsonify({"success": False, "error": "borrow_id, user_id and book_id are required"}), 400

        conn = get_db()
        cur = conn.cursor()
        record = cur.execute(
            "SELECT id FROM borrows WHERE id=? AND user_id=? AND book_id=? AND status='reserved'",
            (borrow_id, user_id, book_id),
        ).fetchone()
        if not record:
            conn.close()
            return jsonify({"success": False, "error": "Reserved book not found"}), 404

        from datetime import datetime, timedelta
        picked_up_at = datetime.now()
        borrowed_at = picked_up_at
        due_date = borrowed_at + timedelta(days=BORROW_DAYS)
        cur.execute(
            """UPDATE borrows
               SET status='borrowed', borrow_date=?, due_date=?
               WHERE id=?""",
            (borrowed_at.isoformat(), due_date.isoformat(), borrow_id),
        )
        cur.execute(
            """UPDATE transactions
               SET status='borrowed', borrowed_at=?, due_date=?, date=?
               WHERE user_id=? AND book_id=? AND status='reserved'""",
            (borrowed_at.isoformat(), due_date.isoformat(), borrowed_at.isoformat(), user_id, book_id),
        )
        cur.execute(
            "UPDATE reservations SET status='picked_up', due_date=? WHERE user_id=? AND book_id=? AND status='reserved'",
            (due_date.isoformat(), user_id, book_id),
        )
        cur.execute("UPDATE books SET available=0 WHERE id=?", (book_id,))
        conn.commit()
        conn.close()
        return jsonify({
            "success": True,
            "pickedUpAt": picked_up_at.isoformat(),
            "borrowed_date": borrowed_at.isoformat(),
            "due_date": due_date.isoformat(),
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/return", methods=["POST"])
def return_book():
    try:
        data = request.get_json()
        borrow_id = data.get("borrow_id")
        book_id = data.get("book_id")
        conn = get_db()
        cur = conn.cursor()
        from datetime import datetime
        returned_at = datetime.now().isoformat()
        cur.execute(
            "UPDATE borrows SET status='returned', return_date=? WHERE id=?",
            (returned_at, borrow_id)
        )
        cur.execute(
            "UPDATE transactions SET status='returned', date=? WHERE user_id=? AND book_id=? AND status='borrowed'",
            (returned_at, data.get("user_id"), book_id)
        )
        cur.execute(
            "UPDATE reservations SET status='returned' WHERE user_id=? AND book_id=? AND status='picked_up'",
            (data.get("user_id"), book_id)
        )
        cur.execute("UPDATE books SET available=1 WHERE id=?", (book_id,))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "returnedAt": returned_at})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/history", methods=["GET"])
@require_auth
def history():
    db = get_db()
    rows = db.execute("""
        SELECT t.id, t.status, t.date, t.borrowed_at, t.due_date,
               b.id as book_id, b.title, b.author, b.image_url, b.price, b.category
        FROM transactions t
        JOIN books b ON t.book_id = b.id
        WHERE t.user_id = ?
        ORDER BY t.date DESC
    """, (g.user_id,)).fetchall()

    return success({"history": [dict(r) for r in rows]})

@app.route("/overdue/<int:user_id>", methods=["GET"])
@require_auth
def overdue(user_id):
    if user_id != g.user_id:
        return error("Forbidden", 403)

    db = get_db()
    now = datetime.now(timezone.utc)
    rows = db.execute("""
        SELECT t.id, t.borrowed_at, t.due_date,
               b.id as book_id, b.title, b.author, b.image_url, b.price, b.category
        FROM transactions t
        JOIN books b ON t.book_id = b.id
        WHERE t.user_id = ? AND t.status = 'borrowed' AND t.due_date IS NOT NULL
    """, (user_id,)).fetchall()

    overdue_list = []
    for r in rows:
        due = datetime.fromisoformat(r["due_date"].replace("Z", "+00:00"))
        if due.tzinfo is None:
            due = due.replace(tzinfo=timezone.utc)
        if now > due:
            days = (now - due).days
            item = dict(r)
            item["days_overdue"] = days
            overdue_list.append(item)

    return success({"overdue": overdue_list})

# ─── RECOMMENDATIONS ────────────────────────────────────────────────────────

def category_recommendations(db, user_id, categories=None, limit=10):
    ensure_borrows_table()
    borrowed_rows = db.execute(
        "SELECT DISTINCT book_id FROM borrows WHERE user_id = ?",
        (user_id,),
    ).fetchall()
    borrowed_ids = {row["book_id"] for row in borrowed_rows}

    if categories is None:
        category_rows = db.execute("""
            SELECT DISTINCT b.category
            FROM borrows br
            JOIN books b ON br.book_id = b.id
            WHERE br.user_id = ?
        """, (user_id,)).fetchall()
        categories = [row["category"] for row in category_rows]

    categories = [category for category in categories if category]
    if not categories:
        return fallback_recommendations(db, borrowed_ids, limit)

    placeholders = ",".join("?" for _ in categories)
    exclude_clause = ""
    params = [user_id, *categories]
    if borrowed_ids:
        exclude_placeholders = ",".join("?" for _ in borrowed_ids)
        exclude_clause = f"AND b.id NOT IN ({exclude_placeholders})"
        params.extend(list(borrowed_ids))

    params.append(limit)
    rows = db.execute(f"""
        SELECT b.id,
               b.title,
               b.author,
               b.category,
               b.image_url,
               b.price,
               COUNT(other.id) as popularity
        FROM books b
        LEFT JOIN borrows other ON other.book_id = b.id AND other.user_id != ?
        WHERE b.category IN ({placeholders})
          {exclude_clause}
        GROUP BY b.id
        ORDER BY popularity DESC, b.title ASC
        LIMIT ?
    """, params).fetchall()

    recs = [
        {
            "id": row["id"],
            "title": row["title"],
            "author": row["author"],
            "category": row["category"],
            "image_url": row["image_url"],
            "price": row["price"],
            "similarity_score": 0.0,
        }
        for row in rows
    ]
    return recs or fallback_recommendations(db, borrowed_ids, limit)

def fallback_recommendations(db, exclude_ids=None, limit=10):
    exclude_ids = set(exclude_ids or [])
    exclude_clause = ""
    params = []
    if exclude_ids:
        exclude_placeholders = ",".join("?" for _ in exclude_ids)
        exclude_clause = f"WHERE b.id NOT IN ({exclude_placeholders})"
        params.extend(list(exclude_ids))

    params.append(limit)
    rows = db.execute(f"""
        SELECT b.id,
               b.title,
               b.author,
               b.category,
               b.image_url,
               b.price,
               COUNT(br.id) as popularity
        FROM books b
        LEFT JOIN borrows br ON br.book_id = b.id
        {exclude_clause}
        GROUP BY b.id
        ORDER BY popularity DESC, b.available DESC, b.title ASC
        LIMIT ?
    """, params).fetchall()

    return [
        {
            "id": row["id"],
            "title": row["title"],
            "author": row["author"],
            "category": row["category"],
            "image_url": row["image_url"],
            "price": row["price"],
            "similarity_score": 0.0,
        }
        for row in rows
    ]

@app.route("/api/recommendations", methods=["POST"])
@require_auth
def api_recommendations():
    body = request.get_json() or {}
    req_user_id = body.get("user_id", g.user_id)
    if int(req_user_id) != g.user_id:
        return error("Forbidden", 403)

    db = get_db()
    recs = category_recommendations(db, g.user_id, body.get("categories"), 10)
    return success({"recommendations": recs})

@app.route("/recommendations", methods=["GET"])
@require_auth
def recommendations():
    db = get_db()
    recs = category_recommendations(db, g.user_id, None, 10)
    return success({"recommendations": recs})

# ─── ADMIN ──────────────────────────────────────────────────────────────────

@app.route("/admin/books", methods=["POST"])
@require_admin
def admin_add_book():
    body = request.get_json() or {}
    title = body.get("title", "").strip()
    author = body.get("author", "").strip()
    category = body.get("category", "").strip()
    image_url = body.get("image_url", "").strip()
    description = body.get("description", "").strip()

    if not title or not author or not category:
        return error("title, author, and category are required")

    if category not in CATEGORY_PRICES:
        return error("category must be one of: Web Development, Data Science, AI/ML, Cybersecurity")

    download_price, rent_price = CATEGORY_PRICES[category]

    db = get_db()
    cur = db.execute(
        """INSERT INTO books
           (title, author, category, price, download_price, rent_price, image_url, description, available)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)""",
        (title, author, category, rent_price, download_price, rent_price, image_url, description),
    )
    db.commit()
    book = db.execute("SELECT * FROM books WHERE id = ?", (cur.lastrowid,)).fetchone()
    return success({"book": dict(book)}), 201

def _pdf_storage_name(book_id: int) -> str:
    """Canonical on-disk name (no spaces, path-safe)."""
    return secure_filename(f"book_{book_id}.pdf")


def _validate_uploaded_pdf(file) -> str | None:
    """Return an error message if the upload is invalid, else None."""
    raw = (file.filename or "").strip()
    if not raw:
        return "No file selected"

    # Normalize path separators; only use the final segment (handles spaces in names).
    base = os.path.basename(raw.replace("\\", "/"))
    if not base or base in (".", ".."):
        return "Invalid filename"
    if ".." in base.split("/"):
        return "Invalid filename"

    # Extension check on the basename (spaces in the name are allowed).
    if not base.lower().endswith(".pdf"):
        return "Only PDF files are allowed"

    return None


@app.route("/admin/upload-pdf/<int:book_id>", methods=["POST"])
def admin_upload_pdf(book_id):
    db = get_db()
    book = db.execute("SELECT id, title FROM books WHERE id = ?", (book_id,)).fetchone()
    if not book:
        return error("Book not found", 404)

    if "file" not in request.files:
        return error("No file uploaded")

    file = request.files["file"]
    validation_error = _validate_uploaded_pdf(file)
    if validation_error:
        return error(validation_error)

    os.makedirs(PDF_DIR, exist_ok=True)
    filename = _pdf_storage_name(book_id)
    filepath = os.path.join(PDF_DIR, filename)
    tmp_path = filepath + ".tmp"

    try:
        file.save(tmp_path)
        if os.path.getsize(tmp_path) == 0:
            os.remove(tmp_path)
            return error("Uploaded file is empty")
        os.replace(tmp_path, filepath)
    except OSError:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        return error("Failed to save PDF", 500)

    db.execute("UPDATE books SET pdf_path = ? WHERE id = ?", (filename, book_id))
    db.commit()

    return success({"message": "PDF uploaded", "pdf_path": filename, "book_title": book["title"]})

@app.route("/admin/books/<int:book_id>", methods=["DELETE"])
@require_admin
def admin_delete_book(book_id):
    db = get_db()
    book = db.execute("SELECT id FROM books WHERE id = ?", (book_id,)).fetchone()
    if not book:
        return error("Book not found", 404)

    active = db.execute(
        "SELECT id FROM transactions WHERE book_id = ? AND status = 'borrowed'",
        (book_id,),
    ).fetchone()
    if active:
        return error("Cannot delete a book that is currently borrowed")

    db.execute("DELETE FROM transactions WHERE book_id = ?", (book_id,))
    db.execute("DELETE FROM reservations WHERE book_id = ?", (book_id,))
    db.execute("DELETE FROM books WHERE id = ?", (book_id,))
    db.commit()
    return success({"message": "Book deleted"})

@app.route("/admin/borrows", methods=["GET"])
@require_admin
def admin_borrows():
    db = get_db()
    rows = db.execute("""
        SELECT t.id, t.status, t.borrowed_at, t.due_date,
               u.id as user_id, u.name as user_name, u.email as user_email,
               b.id as book_id, b.title, b.author, b.category
        FROM transactions t
        JOIN users u ON t.user_id = u.id
        JOIN books b ON t.book_id = b.id
        WHERE t.status = 'borrowed'
        ORDER BY t.due_date ASC
    """).fetchall()
    return success({"borrows": [dict(r) for r in rows]})

# ─── MAIN ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    ensure_borrows_table()
    db = get_db()
    migrate_schema(db)
    seed_admin(db, hash_password)
    db.commit()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
