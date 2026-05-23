# 📚 SmartShelf AI – Intelligent Library Platform

A full-stack, production-level library management system with AI-powered book recommendations using TF-IDF + Cosine Similarity.

---

## 🗂 Project Structure

```
smartshelf/
├── backend/
│   ├── app.py              # Main Flask application
│   ├── database.py         # SQLite setup + seed data (42 books)
│   ├── recommendations.py  # TF-IDF + cosine similarity engine
│   ├── requirements.txt
│   └── test_app.py         # pytest tests
│
└── frontend/
    ├── src/
    │   ├── App.tsx          # Root component + page routing
    │   ├── App.css          # Full design system
    │   ├── AuthContext.tsx  # Global auth state
    │   ├── api.ts           # Typed API client
    │   ├── types/index.ts   # TypeScript interfaces
    │   ├── pages/
    │   │   ├── AuthPage.tsx
    │   │   ├── Dashboard.tsx
    │   │   ├── BooksPage.tsx
    │   │   ├── BorrowedPage.tsx
    │   │   ├── HistoryPage.tsx
    │   │   └── RecommendationsPage.tsx
    │   └── components/
    │       ├── Sidebar.tsx
    │       └── BookCard.tsx
    ├── index.html
    ├── vite.config.ts       # Dev proxy → Flask (no CORS issues)
    ├── package.json
    └── tsconfig.json
```

---

## 🚀 Quick Start

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt

# Start the server
python app.py
```

Backend runs at: **http://localhost:5000**

> SQLite database (`smartshelf.db`) and 42 seed books are created automatically on first run.

---

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend runs at: **http://localhost:3000**

> The Vite dev server proxies all API calls to `http://localhost:5000` — no CORS issues.

---

## 🧪 Running Tests

### Backend Tests (pytest)

```bash
cd backend
source venv/bin/activate
pytest test_app.py -v
```

Tests cover: signup, login, duplicate email, wrong password, borrow, return, history, recommendations.

### Frontend Tests (Vitest)

```bash
cd frontend
npm test
```

Tests cover: API client calls, response format validation, field structure.

---

## 🔌 API Reference

All responses follow this format:
```json
{ "success": true, "data": { ... } }
{ "success": false, "error": "message" }
```

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/signup` | Register new user |
| POST | `/login` | Authenticate user |
| GET | `/books` | List all books |
| POST | `/borrow` | Borrow a book |
| POST | `/return` | Return a book |
| GET | `/history/<user_id>` | Transaction history |
| GET | `/recommendations/<user_id>` | AI recommendations |

### Example Requests

**Signup**
```bash
curl -X POST http://localhost:5000/signup \
  -H "Content-Type: application/json" \
  -d '{"name": "Rahul Sharma", "email": "rahul@example.com", "password": "pass123"}'
```

**Login**
```bash
curl -X POST http://localhost:5000/login \
  -H "Content-Type: application/json" \
  -d '{"email": "rahul@example.com", "password": "pass123"}'
```

**Get Books**
```bash
curl http://localhost:5000/books
```

**Borrow Book**
```bash
curl -X POST http://localhost:5000/borrow \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "book_id": 3}'
```

**Return Book**
```bash
curl -X POST http://localhost:5000/return \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "book_id": 3}'
```

**Get Recommendations**
```bash
curl http://localhost:5000/recommendations/1
```

---

## 🤖 AI Recommendation Engine

- **Algorithm**: Content-based filtering with TF-IDF + Cosine Similarity
- **Input features**: title + author + category + description
- **Logic**:
  1. Builds TF-IDF matrix for all books
  2. Creates a user preference vector by averaging vectors of borrowed books
  3. Computes cosine similarity between user vector and all books
  4. Returns top 5 most similar books, excluding currently borrowed ones
  5. Falls back to popular available books for new users

---

## 📚 Book Catalogue

42 real books across 6 categories (7 per category):
- **Tech** – Clean Code, Pragmatic Programmer, Design Patterns, etc.
- **AI/ML** – Hands-On ML, Deep Learning, AI: A Modern Approach, etc.
- **Data Science** – Python for Data Analysis, Data Science from Scratch, etc.
- **Web Development** – JavaScript: The Good Parts, You Don't Know JS, etc.
- **Money & Finance** – Rich Dad Poor Dad, The Intelligent Investor, etc.
- **Psychology** – Thinking Fast and Slow, Atomic Habits, Influence, etc.

---

## 💳 Payment (Simulated)

- Shows ₹ pricing per book
- Simulates UPI/Card payment with a 1.2s loading modal
- Displays success toast after payment confirmation

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.10+, Flask 3, SQLite |
| AI/ML | scikit-learn (TF-IDF, Cosine Similarity), NumPy |
| Frontend | React 18, TypeScript, Vite |
| Styling | Custom CSS with CSS variables (no UI framework) |
| Testing | pytest (backend), Vitest (frontend) |

---

## ⚙️ Environment Notes

- No `.env` files required — runs out of the box
- SQLite database auto-created at `backend/smartshelf.db`
- Vite proxy handles CORS in development
- For production: add JWT auth, use PostgreSQL, deploy behind nginx
