import sqlite3
import os

DB_PATH = "smartshelf.db"

# (title, author, category, download_price, rent_price, image_url, description)
BOOKS = [
    # Web Development — download ₹29, rent ₹99
    ("Web Development Essentials", "NC State University", "Web Development", 29, 99,
     "https://covers.openlibrary.org/b/id/8231283-L.jpg", "Core concepts for modern web development."),
    ("Web Accessibility for Developers", "Jon Gibbins", "Web Development", 29, 99,
     "https://covers.openlibrary.org/b/id/8231178-L.jpg", "Build accessible websites for everyone."),
    ("Web Design Basics", "Saylor Academy", "Web Development", 29, 99,
     "https://covers.openlibrary.org/b/id/8108233-L.jpg", "Foundational visual design for the web."),
    ("Building Blocks of Responsive Web Design", "Syncfusion", "Web Development", 29, 99,
     "https://covers.openlibrary.org/b/id/7965341-L.jpg", "Responsive layout techniques and patterns."),
    ("Introduction to Web Development", "Wikibooks Contributors", "Web Development", 29, 99,
     "https://covers.openlibrary.org/b/id/8231857-L.jpg", "Beginner-friendly web development introduction."),
    ("HTML5 and CSS3 Responsive Web Design Cookbook", "Benjamin LaGrone", "Web Development", 29, 99,
     "https://covers.openlibrary.org/b/id/10519908-L.jpg", "Practical responsive HTML5 and CSS3 recipes."),
    ("Responsive Web Design", "Ethan Marcotte", "Web Development", 29, 99,
     "https://covers.openlibrary.org/b/id/8091016-L.jpg", "Design websites that adapt to any screen."),
    ("Front-end Developer Handbook 2019", "Cody Lindley", "Web Development", 29, 99,
     "https://covers.openlibrary.org/b/id/8158422-L.jpg", "Overview of modern front-end development."),
    ("Full Stack Development", "BOC Editorial Team", "Web Development", 29, 99,
     "https://covers.openlibrary.org/b/id/8231283-L.jpg", "Client, server, and deployment fundamentals."),
    ("Eloquent JavaScript", "Marijn Haverbeke", "Web Development", 29, 99,
     "https://covers.openlibrary.org/b/id/8231857-L.jpg", "Modern JavaScript programming from the ground up."),
    ("JavaScript Notes for Professionals", "GoalKicker", "Web Development", 29, 99,
     "https://covers.openlibrary.org/b/id/8231178-L.jpg", "Quick-reference JavaScript for developers."),
    ("UI Full Stack Web Development", "Simplilearn", "Web Development", 29, 99,
     "https://covers.openlibrary.org/b/id/8091016-L.jpg", "UI and full-stack web development skills."),

    # Data Science — download ₹39, rent ₹119
    ("The Handbook of Data Analysis", "Handbook Contributors", "Data Science", 39, 119,
     "https://covers.openlibrary.org/b/id/10519908-L.jpg", "Methods and practices for data analysis."),
    ("Introduction to Data Analysis Handbook", "UC Berkeley", "Data Science", 39, 119,
     "https://covers.openlibrary.org/b/id/8231857-L.jpg", "Introductory handbook to data analysis."),
    ("Introduction to Data Analysis with R", "Matthias Kohl", "Data Science", 39, 119,
     "https://covers.openlibrary.org/b/id/8108233-L.jpg", "Data analysis using the R language."),
    ("Mathematical Foundations for Data Analysis", "Jeff M. Phillips", "Data Science", 39, 119,
     "https://covers.openlibrary.org/b/id/7965341-L.jpg", "Mathematical foundations for analyzing data."),
    ("Advanced Data Analysis from an Elementary Point of View", "Cosma Shalizi", "Data Science", 39, 119,
     "https://covers.openlibrary.org/b/id/8231178-L.jpg", "Advanced analysis from first principles."),
    ("Open Data Structures", "Pat Morin", "Data Science", 39, 119,
     "https://covers.openlibrary.org/b/id/8231283-L.jpg", "Open-source approach to data structures."),
    ("Social Data Analysis", "Various Authors", "Data Science", 39, 119,
     "https://covers.openlibrary.org/b/id/8158422-L.jpg", "Analyzing social and behavioral data."),
    ("Computational Topology for Data Analysis", "Tamal K. Dey", "Data Science", 39, 119,
     "https://covers.openlibrary.org/b/id/8091016-L.jpg", "Topology methods for modern data analysis."),

    # AI/ML — download ₹49, rent ₹139
    ("Artificial Intelligence", "Various Authors", "AI/ML", 49, 139,
     "https://covers.openlibrary.org/b/id/10519908-L.jpg", "Broad introduction to artificial intelligence."),
    ("Introduction to Artificial Intelligence", "Wolfgang Ertel", "AI/ML", 49, 139,
     "https://covers.openlibrary.org/b/id/8231283-L.jpg", "Foundational AI concepts and methods."),
    ("Student Guide to Artificial Intelligence", "IBM", "AI/ML", 49, 139,
     "https://covers.openlibrary.org/b/id/8231178-L.jpg", "Student-oriented guide to AI fundamentals."),
    ("Artificial Intelligence Technology", "Various Authors", "AI/ML", 49, 139,
     "https://covers.openlibrary.org/b/id/8108233-L.jpg", "Survey of AI technologies and applications."),
    ("Foundations of Machine Learning", "Mehryar Mohri", "AI/ML", 49, 139,
     "https://covers.openlibrary.org/b/id/7965341-L.jpg", "Theoretical foundations of machine learning."),
    ("Machine Learning", "Various Authors", "AI/ML", 49, 139,
     "https://covers.openlibrary.org/b/id/8231857-L.jpg", "Core machine learning principles and practice."),
    ("Interpretable Machine Learning", "Christoph Molnar", "AI/ML", 49, 139,
     "https://covers.openlibrary.org/b/id/8158422-L.jpg", "Making machine learning models understandable."),
    ("Mathematics for Machine Learning", "Marc Peter Deisenroth", "AI/ML", 49, 139,
     "https://covers.openlibrary.org/b/id/8091016-L.jpg", "Mathematics needed for machine learning."),
    ("Understanding Deep Learning", "Simon J.D. Prince", "AI/ML", 49, 139,
     "https://covers.openlibrary.org/b/id/8231283-L.jpg", "Modern deep learning concepts explained clearly."),
    ("Neural Networks and Deep Learning", "Michael Nielsen", "AI/ML", 49, 139,
     "https://covers.openlibrary.org/b/id/10519908-L.jpg", "Neural networks and deep learning fundamentals."),
    ("The Little Book of Deep Learning", "Francois Fleuret", "AI/ML", 49, 139,
     "https://covers.openlibrary.org/b/id/8231178-L.jpg", "Concise introduction to deep learning."),
    ("Speech and Language Processing", "Dan Jurafsky", "AI/ML", 49, 139,
     "https://covers.openlibrary.org/b/id/8108233-L.jpg", "Speech and NLP foundations and techniques."),
    ("Natural Language Processing", "Various Authors", "AI/ML", 49, 139,
     "https://covers.openlibrary.org/b/id/7965341-L.jpg", "Overview of natural language processing."),
    ("Foundations of Large Language Models", "Tong Xiao", "AI/ML", 49, 139,
     "https://covers.openlibrary.org/b/id/8231857-L.jpg", "Foundations behind large language models."),
    ("Prompt Engineering", "Various Authors", "AI/ML", 49, 139,
     "https://covers.openlibrary.org/b/id/8158422-L.jpg", "Techniques for effective prompt engineering."),
    ("Programming Computer Vision with Python", "Jan Erik Solem", "AI/ML", 49, 139,
     "https://covers.openlibrary.org/b/id/8091016-L.jpg", "Computer vision programming with Python."),
    ("Machine Learning with Python", "Various Authors", "AI/ML", 49, 139,
     "https://covers.openlibrary.org/b/id/8231283-L.jpg", "Practical machine learning using Python."),
    ("Algorithms for Reinforcement Learning", "Csaba Szepesvari", "AI/ML", 49, 139,
     "https://covers.openlibrary.org/b/id/8231178-L.jpg", "Algorithms for reinforcement learning."),

    # Cybersecurity — download ₹49, rent ₹149
    ("Ethical Hacking", "Various Authors", "Cybersecurity", 49, 149,
     "https://covers.openlibrary.org/b/id/8091016-L.jpg", "Ethical hacking principles and practice."),
    ("Penetration Testing: A Hands-On Introduction to Hacking", "Georgia Weidman", "Cybersecurity", 49, 149,
     "https://covers.openlibrary.org/b/id/8158422-L.jpg", "Hands-on introduction to penetration testing."),
    ("The Basics of Hacking and Penetration Testing", "Patrick Engebretson", "Cybersecurity", 49, 149,
     "https://covers.openlibrary.org/b/id/8231283-L.jpg", "Basics of hacking and penetration testing."),
    ("Penetration Testing Guidance", "CREST", "Cybersecurity", 49, 149,
     "https://covers.openlibrary.org/b/id/10519908-L.jpg", "Industry guidance on penetration testing."),
    ("OWASP Web Security Testing Guide", "OWASP Foundation", "Cybersecurity", 49, 149,
     "https://covers.openlibrary.org/b/id/8231857-L.jpg", "Web application security testing guide."),
    ("Digital Forensics", "Various Authors", "Cybersecurity", 49, 149,
     "https://covers.openlibrary.org/b/id/8108233-L.jpg", "Digital forensics methods and workflows."),
    ("Hacking Secret Ciphers with Python", "Al Sweigart", "Cybersecurity", 49, 149,
     "https://covers.openlibrary.org/b/id/7965341-L.jpg", "Cryptography and ciphers with Python."),
    ("Kali Linux Reference Guide", "Offensive Security", "Cybersecurity", 49, 149,
     "https://covers.openlibrary.org/b/id/8231178-L.jpg", "Reference guide for Kali Linux security tools."),
    ("Technical Guide to Information Security Testing", "NIST", "Cybersecurity", 49, 149,
     "https://covers.openlibrary.org/b/id/8231283-L.jpg", "NIST guide to information security testing."),
]

# Additional titles inserted on startup if not already present (preserves pdf_path on existing rows).
MISSING_BOOKS = [
    # AI/ML — download ₹49, rent ₹139
    ("Mitigating Bias in Artificial Intelligence", "Various Authors", "AI/ML", 49, 139,
     "https://covers.openlibrary.org/b/id/8231283-L.jpg", "Addressing bias in AI systems."),
    ("Artificial Intelligence and Privacy", "Various Authors", "AI/ML", 49, 139,
     "https://covers.openlibrary.org/b/id/8231178-L.jpg", "AI and privacy considerations."),
    ("Machine Learning Supervised Techniques", "Various Authors", "AI/ML", 49, 139,
     "https://covers.openlibrary.org/b/id/8108233-L.jpg", "Supervised machine learning techniques."),
    ("Undergraduate Fundamentals of Machine Learning", "Various Authors", "AI/ML", 49, 139,
     "https://covers.openlibrary.org/b/id/7965341-L.jpg", "Undergraduate ML fundamentals."),
    ("Mathematical Analysis of Machine Learning Algorithms", "Various Authors", "AI/ML", 49, 139,
     "https://covers.openlibrary.org/b/id/8231857-L.jpg", "Mathematical analysis of ML algorithms."),
    ("Machine Learning with Python Tutorial", "Various Authors", "AI/ML", 49, 139,
     "https://covers.openlibrary.org/b/id/8158422-L.jpg", "Machine learning with Python tutorial."),
    ("Python Machine Learning Projects", "Various Authors", "AI/ML", 49, 139,
     "https://covers.openlibrary.org/b/id/8091016-L.jpg", "Hands-on Python ML projects."),
    ("An Introduction to Deep Reinforcement Learning", "Various Authors", "AI/ML", 49, 139,
     "https://covers.openlibrary.org/b/id/10519908-L.jpg", "Introduction to deep reinforcement learning."),
    ("Introduction to Reinforcement Learning", "Various Authors", "AI/ML", 49, 139,
     "https://covers.openlibrary.org/b/id/8231283-L.jpg", "Foundations of reinforcement learning."),
    ("Deep Learning Algorithms", "Various Authors", "AI/ML", 49, 139,
     "https://covers.openlibrary.org/b/id/8231178-L.jpg", "Survey of deep learning algorithms."),
    ("Artificial Intelligence Index Report 2024", "Stanford HAI", "AI/ML", 49, 139,
     "https://covers.openlibrary.org/b/id/8108233-L.jpg", "Stanford HAI AI Index Report 2024."),
    ("Deep Learning in Computer Vision", "Various Authors", "AI/ML", 49, 139,
     "https://covers.openlibrary.org/b/id/7965341-L.jpg", "Deep learning for computer vision."),
    ("Clustering Algorithms A Comparative Approach", "Various Authors", "AI/ML", 49, 139,
     "https://covers.openlibrary.org/b/id/8231857-L.jpg", "Comparative study of clustering algorithms."),
    ("Mathematics for Machine Learning", "Marc Peter Deisenroth", "AI/ML", 49, 139,
     "https://covers.openlibrary.org/b/id/8091016-L.jpg", "Mathematics needed for machine learning."),
    ("Understanding Deep Learning", "Simon J.D. Prince", "AI/ML", 49, 139,
     "https://covers.openlibrary.org/b/id/8231283-L.jpg", "Modern deep learning concepts explained clearly."),

    # Data Science — download ₹39, rent ₹119
    ("Introduction to Statistics and Data Analysis for Physicists", "Gerhard Bohm", "Data Science", 39, 119,
     "https://covers.openlibrary.org/b/id/8231178-L.jpg", "Statistics and data analysis for physicists."),
    ("Data Analysis in the Psychological Sciences", "Various Authors", "Data Science", 39, 119,
     "https://covers.openlibrary.org/b/id/8108233-L.jpg", "Data analysis in psychology."),
    ("Advanced Data Analysis from an Elementary Point of View", "Cosma Shalizi", "Data Science", 39, 119,
     "https://covers.openlibrary.org/b/id/8231178-L.jpg", "Advanced analysis from first principles."),
    ("Computational Topology for Data Analysis", "Tamal K. Dey", "Data Science", 39, 119,
     "https://covers.openlibrary.org/b/id/8091016-L.jpg", "Topology methods for modern data analysis."),

    # Cybersecurity — download ₹49, rent ₹149
    ("Penetration Testing Guidance", "CREST", "Cybersecurity", 49, 149,
     "https://covers.openlibrary.org/b/id/10519908-L.jpg", "Industry guidance on penetration testing."),
    ("A Guide for Running an Effective Penetration Testing Programme", "CREST", "Cybersecurity", 49, 149,
     "https://covers.openlibrary.org/b/id/8231857-L.jpg", "Running an effective penetration testing programme."),
    ("Hacking Techniques in Wired Networks", "Various Authors", "Cybersecurity", 49, 149,
     "https://covers.openlibrary.org/b/id/8108233-L.jpg", "Hacking techniques in wired networks."),
    ("Computer Hacking as a Social Problem", "Various Authors", "Cybersecurity", 49, 149,
     "https://covers.openlibrary.org/b/id/7965341-L.jpg", "Social dimensions of computer hacking."),
    ("Technical Guide to Information Security Testing", "NIST", "Cybersecurity", 49, 149,
     "https://covers.openlibrary.org/b/id/8231283-L.jpg", "NIST guide to information security testing."),
]


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _column_names(db, table):
    return {row[1] for row in db.execute(f"PRAGMA table_info({table})").fetchall()}


def migrate_schema(db):
    """Add missing columns/tables without wiping existing data."""
    user_cols = _column_names(db, "users")
    if "is_admin" not in user_cols:
        db.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0")

    tx_cols = _column_names(db, "transactions")
    if "due_date" not in tx_cols:
        db.execute("ALTER TABLE transactions ADD COLUMN due_date TEXT")
    if "borrowed_at" not in tx_cols:
        db.execute("ALTER TABLE transactions ADD COLUMN borrowed_at TEXT")
    if "borrow_type" not in tx_cols:
        db.execute("ALTER TABLE transactions ADD COLUMN borrow_type TEXT DEFAULT 'hard copy'")
    if "pickup_deadline" not in tx_cols:
        db.execute("ALTER TABLE transactions ADD COLUMN pickup_deadline TEXT")
    if "reserved_date" not in tx_cols:
        db.execute("ALTER TABLE transactions ADD COLUMN reserved_date TEXT")

    db.execute("""
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            book_id INTEGER NOT NULL,
            reservation_id TEXT UNIQUE NOT NULL,
            status TEXT NOT NULL DEFAULT 'reserved',
            reservation_date TEXT NOT NULL,
            due_date TEXT NOT NULL,
            amount_paid INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    book_cols = _column_names(db, "books")
    if book_cols:
        if "download_price" not in book_cols:
            db.execute("ALTER TABLE books ADD COLUMN download_price INTEGER NOT NULL DEFAULT 29")
        if "rent_price" not in book_cols:
            db.execute("ALTER TABLE books ADD COLUMN rent_price INTEGER NOT NULL DEFAULT 99")
        if "pdf_path" not in book_cols:
            db.execute("ALTER TABLE books ADD COLUMN pdf_path TEXT")
        if "price" not in book_cols:
            db.execute("ALTER TABLE books ADD COLUMN price INTEGER NOT NULL DEFAULT 99")


def ensure_books_table(db):
    db.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            category TEXT NOT NULL,
            price INTEGER NOT NULL,
            download_price INTEGER NOT NULL,
            rent_price INTEGER NOT NULL,
            image_url TEXT,
            description TEXT,
            pdf_path TEXT,
            available INTEGER DEFAULT 1
        )
    """)


def _insert_books(db, rows):
    db.executemany(
        """INSERT INTO books
           (title, author, category, price, download_price, rent_price, image_url, description, pdf_path, available)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, 1)""",
        [(t, a, c, rent, dl, rent, img, desc) for t, a, c, dl, rent, img, desc in rows],
    )


def seed_books_if_empty(db):
    count = db.execute("SELECT COUNT(*) FROM books").fetchone()[0]
    if count == 0:
        _insert_books(db, BOOKS)
        print(f"Seeded {len(BOOKS)} books across 4 categories")


def insert_missing_books(db):
    """Insert catalog titles that are not yet in the database (keeps existing pdf_path rows)."""
    existing = {row[0] for row in db.execute("SELECT title FROM books").fetchall()}
    to_add = [b for b in MISSING_BOOKS if b[0] not in existing]
    if to_add:
        _insert_books(db, to_add)
        print(f"Inserted {len(to_add)} missing book(s)")


def reset_and_seed_books(db):
    """Drop and recreate books only — use manually; not called on normal startup."""
    db.execute("DROP TABLE IF EXISTS books")
    ensure_books_table(db)
    _insert_books(db, BOOKS)
    print(f"Seeded {len(BOOKS)} books across 4 categories")


def seed_admin(db, hash_password_fn):
    existing = db.execute(
        "SELECT id FROM users WHERE email = ?", ("admin@smartshelf.com",)
    ).fetchone()
    if not existing:
        db.execute(
            "INSERT INTO users (name, email, password, is_admin) VALUES (?, ?, ?, 1)",
            ("Admin", "admin@smartshelf.com", hash_password_fn("admin123")),
        )


def init_db():
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            is_admin INTEGER NOT NULL DEFAULT 0
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            book_id INTEGER NOT NULL,
            status TEXT NOT NULL,
            date TEXT NOT NULL,
            borrowed_at TEXT,
            due_date TEXT,
            borrow_type TEXT DEFAULT 'hard copy',
            pickup_deadline TEXT,
            reserved_date TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    db.commit()

    ensure_books_table(db)
    migrate_schema(db)
    seed_books_if_empty(db)
    insert_missing_books(db)
    db.commit()
    print("Database ready")
