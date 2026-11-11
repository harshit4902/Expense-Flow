# ExpenseFlow 💰📊
> **AI-Powered Multilingual Personal Expense, Income & Savings Tracker**

ExpenseFlow is a production-ready personal finance management web application built with **FastAPI (Python 3.12+)**, **React (Vite + Tailwind CSS)**, and **Turso (LibSQL / SQLite)**. It empowers users to manage expenses, income, automated savings rollovers, monthly budgets, and interactive visual reports with financial calculation accuracy (stored as integer paise). It features an **AI Assistant with Speech-to-Text (Microphone)** supporting both English and Hindi/Hinglish.

---

## 🌟 Key Features

### 1. 🤖 AI Chat Assistant with Multilingual Speech-to-Text (Mic)
- **Natural Language Parsing**: Speak or type natural language financial entries (e.g., *"Spent 120 on coffee"*, *"Got 50,000 salary today"*, *"Dost ko 500 diye dinner ke liye"*, *"Saved 2000 in emergency fund"*).
- **Speech-to-Text (STT) Microphone**: In-browser voice input supporting both **English (`en-IN`)** and **Hindi (`hi-IN`)** with single-click language toggle.
- **Multilingual Support**: Supports English, pure Hindi (Devanagari), and conversational Hinglish.
- **Smart Category Auto-Mapping & Semantic Matching**: Matches common daily items (chai, samosa, rent, petrol, groceries, gym) to appropriate expense or income categories.
- **Global Floating Chat Widget & Dedicated Page**: Accessible everywhere in the app via the bottom-right floating widget or dedicated AI Assistant view.
- **Resilient Fallback**: Uses OpenAI with an integrated zero-quota rule-based multilingual fallback parser ensuring 100% uptime.

### 2. 🔐 User Authentication & Security
- Secure Argon2 password hashing using `pwdlib`.
- JWT Bearer token authentication with automatic route protection and 401 handling.
- **Enhanced Signup & Login**:
  - Separate **Password** and **Confirm Password** fields on registration.
  - Interactive **Eye Toggle Buttons** to show/hide passwords.
- Strict user-level data isolation across all financial entries, categories, budgets, and savings ledgers.

### 3. 💸 Income & Expense Management
- Record income and expense entries with description, category, and date.
- **Integer Paise Storage**: All currency is stored as integer paise (e.g. ₹250.50 = 25050 paise) preventing floating-point inaccuracies.
- **Prelisted Minimal Categories**: Automatically auto-seeds standard income and expense categories (Food & Dining, Groceries, Rent, Salary, Freelance, etc.) on first login.
- Category-to-transaction type validation (prevents assigning an expense to an income category).
- Search, filter by type/category/date range, and pagination.

### 4. 🐷 Dedicated Savings Module & Month-End Rollover
- **Independent Savings Reserve**: Income is not automatically counted as savings, nor are expenses subtracted from savings.
- **Automated Month-End Rollover**: When the month changes, remaining net monthly balance ($\text{Income} - \text{Expenses}$) is automatically deposited into a designated rollover reserve: `"{Month Name} {Year} Saving"`.
- **Ledger-Based Accounting**:
  $$\text{Current Savings} = \text{Initial Savings} + \sum \text{Deposits} - \sum \text{Withdrawals} + \sum \text{Net Adjustments}$$
- **Initial Setup**: First-time account opening balance.
- **Overdraft-Protected Withdrawals**: Strict checks prevent withdrawing more than the available savings balance.
- **Audit-Logged True-Ups (Adjustments)**: Corrects tracked balances to match real-world bank statements while preserving complete audit history.

### 5. 🎯 Monthly Budgets & Threshold Alerts
- Set monthly spending limits for overall spending or specific expense categories.
- Real-time utilization calculation and remaining allowance metrics.
- Proactive threshold warnings:
  - 🟡 **Warning**: $\ge 80\%$ budget consumed.
  - 🔴 **Exceeded**: $> 100\%$ budget spent.
- Prevents double-counting between overall and sub-category budgets.

### 6. 📊 Visual Dashboard & Monthly Reports
- **Month & Year Selector on Expense Breakdown**: Filter and inspect category-wise pie charts for any selected month and year.
- **Income vs. Expense Trends**: 6-month comparative bar charts (Recharts).
- **Savings Timeline**: Real-time savings reserve tracker.
- **Detailed Monthly Reports**: Calculates savings rate percentage ($(\text{net\_savings} / \text{income}) \times 100$) and daily spending velocity.

### 7. 📱 Fully Responsive Design
- Compatible across **mobile phones, tablets, laptops, and desktops**.
- Mobile navigation drawer with backdrop blur overlay and quick hamburger toggle.
- Responsive data tables with horizontal scroll wrappers and mobile-friendly modal popups.

---

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.12+)
- **Database**: Turso (LibSQL) Cloud Database & local SQLite
- **ORM & Migrations**: SQLAlchemy 2.0 & Alembic
- **Security**: Argon2 (`pwdlib[argon2]`), JWT (`python-jose[cryptography]`)
- **AI & NLP**: OpenAI API (`gpt-4o-mini`) + Multilingual Semantic Fallback Engine
- **Testing**: Pytest & HTTPX TestClient (35 automated tests)

### Frontend
- **Framework**: React 18
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **Charts**: Recharts
- **Icons**: Lucide React
- **Speech Recognition**: Web Speech API (`SpeechRecognition` / `webkitSpeechRecognition`)
- **HTTP Client**: Axios with JWT interceptors

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.12+
- Node.js 18+ & npm
- *(Optional)* Turso CLI or cloud database account
- *(Optional)* OpenAI API Key

---

### 2. Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables (`backend/.env`):
   ```env
   PROJECT_NAME="ExpenseFlow"
   ENV="development"
   DEBUG=True
   API_V1_STR="/api/v1"

   # Local SQLite:
   DATABASE_URL="sqlite:///./expenseflow.db"

   # Or Turso Cloud Database:
   # TURSO_DATABASE_URL="libsql://your-db-org.turso.io"
   # TURSO_AUTH_TOKEN="your-turso-jwt-token"

   SECRET_KEY="your-super-secret-jwt-key-32charsmin!"
   ALGORITHM="HS256"
   ACCESS_TOKEN_EXPIRE_MINUTES=1440

   # Optional for OpenAI AI Assistant:
   OPENAI_API_KEY="sk-..."
   OPENAI_MODEL="gpt-4o-mini"
   ```

5. Run database migrations:
   ```bash
   alembic upgrade head
   ```

6. Run automated test suite:
   ```bash
   pytest -v
   ```

7. Start the FastAPI development server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   - API Server: `http://localhost:8000`
   - Interactive Swagger API Docs: `http://localhost:8000/docs`
   - Health Check: `http://localhost:8000/health`

---

### 3. Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. *(Optional)* Create `.env` for production API URL:
   ```env
   VITE_API_URL=http://localhost:8000
   ```
   *(In local development, Vite automatically proxies `/api` requests to `http://localhost:8000`)*

4. Start Vite development server:
   ```bash
   npm run dev
   ```

5. Open your browser and navigate to:
   👉 **`http://localhost:3000`**

---

## ☁️ Deployment Guide (Render)

### Backend (Web Service)
- **Environment**: Python
- **Root Directory**: `backend` (or build from root: `cd backend`)
- **Python Version**: `3.12.11` (configured via `.python-version`)
- **Build Command**:
  ```bash
  pip install --upgrade pip && pip install -r requirements.txt
  ```
- **Start Command**:
  ```bash
  uvicorn app.main:app --host 0.0.0.0 --port $PORT
  ```
- **Health Check Path**: `/health`
- **Required Environment Variables**:
  - `TURSO_DATABASE_URL`: `libsql://your-db.turso.io`
  - `TURSO_AUTH_TOKEN`: `your-turso-token`
  - `SECRET_KEY`: `your-32-char-random-secret`
  - `OPENAI_API_KEY`: *(optional)*

### Frontend (Static Site)
- **Build Command**: `npm run build`
- **Publish Directory**: `dist`
- **Environment Variables**:
  - `VITE_API_URL`: `https://your-backend-api.onrender.com`

---

## 📡 API Reference Overview

All API endpoints are prefixed with `/api/v1`:

### Authentication & User
- `POST /api/v1/auth/register`: Create user account & receive JWT token
- `POST /api/v1/auth/login`: Authenticate credentials & receive JWT token
- `GET /api/v1/auth/me`: Retrieve current profile & account status

### AI Assistant
- `POST /api/v1/ai/chat`: Parse natural language text or STT voice transcript to automatically create transactions, savings deposits, or budget queries (English & Hindi/Hinglish).
- `GET /api/v1/ai/history`: Retrieve recent chat message history.

### Categories
- `GET /api/v1/categories`: Retrieve categories (auto-seeds defaults on first call)
- `POST /api/v1/categories`: Create custom category
- `PUT /api/v1/categories/{id}`: Update category name
- `DELETE /api/v1/categories/{id}`: Delete unused category

### Transactions
- `GET /api/v1/transactions`: Filtered, searched, and paginated transactions
- `POST /api/v1/transactions`: Create income or expense entry
- `GET /api/v1/transactions/{id}`: Get single transaction details
- `PUT /api/v1/transactions/{id}`: Update transaction
- `DELETE /api/v1/transactions/{id}`: Delete transaction

### Savings Ledger
- `GET /api/v1/savings/summary`: Current balance, initial savings, and totals
- `GET /api/v1/savings/history`: Chronological savings ledger entries
- `POST /api/v1/savings/initialize`: Establish initial savings balance
- `POST /api/v1/savings/deposit`: Record manual savings deposit
- `POST /api/v1/savings/withdraw`: Overdraft-protected withdrawal
- `PATCH /api/v1/savings/balance`: Balance adjustment / true-up

### Monthly Budgets
- `GET /api/v1/budgets`: Monthly budget summary and utilization percentages
- `POST /api/v1/budgets`: Create overall or category budget
- `PUT /api/v1/budgets/{id}`: Update budget amount
- `DELETE /api/v1/budgets/{id}`: Delete budget

### Dashboard & Analytics
- `GET /api/v1/dashboard/summary`: Top-level income, expense, savings, and budget cards
- `GET /api/v1/dashboard/category-breakdown?month={m}&year={y}`: Category expense pie chart with month/year selector
- `GET /api/v1/dashboard/monthly-trends`: Past $N$ months comparison
- `GET /api/v1/dashboard/savings-trends`: Running balance history
- `GET /api/v1/reports/monthly`: Statement, savings rate, and daily spending velocity

---

## 🧪 Testing

Run the automated test suite covering all modules:

```bash
cd backend
pytest -v
```

**Test Coverage (35 automated tests passing)**:
- User registration, duplicate email rejection, and validation
- Argon2 hashing & JWT authorization
- Multilingual AI chat parsing (English & Hindi/Hinglish)
- Category isolation, seeding, and deletion protection
- Integer paise financial calculations & transaction CRUD
- Savings ledger, overdraft prevention, and balance adjustments
- Automated month-end net savings rollover
- Budget warnings (80% warning & 100% exceeded triggers)
- Dashboard aggregation & monthly reports

---

## 📜 License
MIT License. Built as a comprehensive personal finance and AI application.
