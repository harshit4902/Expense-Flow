# ExpenseFlow 💰📊
> **AI-Powered Personal Expense, Income & Savings Tracker**

ExpenseFlow is a personal finance management web application built with **FastAPI (Python 3.11+)** and **React (Vite + Tailwind CSS)**. It empowers users to track income, expenses, custom categories, monthly budgets, and dedicated savings accounts with financial calculation accuracy (stored as integer paise).

---

## 🌟 Key Features

1. **User Authentication & Data Isolation**:
   - Secure Argon2 password hashing using `pwdlib`.
   - JWT Bearer token authentication with protected routes.
   - User-level data isolation across all financial records and categories.

2. **Income & Expense Tracking**:
   - Record income and expense entries with description, category, and date.
   - Stored in **integer paise** (e.g., ₹250.50 = 25050 paise) to prevent floating-point rounding errors.
   - Category-to-transaction type validation (e.g. expenses cannot be assigned to an income category).
   - Full filtering by type, category, date range, search query, and pagination.

3. **Dedicated Savings Management Module**:
   - **Independent from ordinary transactions**: Income is not automatically counted as savings, nor are expenses subtracted from savings.
   - Calculates real-time savings using ledger entries:
     $$\text{Current Savings} = \text{Initial Savings} + \sum \text{Deposits} - \sum \text{Withdrawals} + \sum \text{Net Adjustments}$$
   - **Initial Savings Balance**: Optional first-time account setup balance.
   - **Deposits & Overdraft-Protected Withdrawals**: Explicit movements to/from savings.
   - **Balance Adjustments (True-ups)**: Allows users to align tracked savings with real-world bank balances via delta adjustments while maintaining full audit history.

4. **Monthly Budget Management**:
   - Overall monthly spending limits and category-specific budgets.
   - Real-time utilization calculation and remaining budget metrics.
   - Threshold warnings:
     - 🟡 **Warning**: $\ge 80\%$ budget consumed.
     - 🔴 **Exceeded**: $> 100\%$ budget spent.
   - Prevents double-counting between overall and sub-category budgets.

5. **Financial Dashboard & Visual Reports**:
   - Monthly Income vs. Expenses comparison charts (Recharts).
   - Category-wise expense breakdown donut charts with percentages.
   - Savings growth and balance timeline.
   - Detailed monthly reports with savings rate percentage ($(\text{net\_savings} / \text{income}) \times 100$) and day-by-day spending distribution.

---

## 🛠️ Technology Stack

### Backend
- **Language**: Python 3.11+ (Tested on Python 3.13)
- **Framework**: FastAPI
- **Database**: SQLite (with SQLAlchemy 2.0 ORM & Alembic migrations)
- **Security**: Argon2 (`pwdlib[argon2]`), JWT (`python-jose[cryptography]`)
- **Validation**: Pydantic v2 & `pydantic-settings`
- **Testing**: Pytest & HTTPX TestClient (31 automated unit tests)

### Frontend
- **Framework**: React 18
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **Charts**: Recharts
- **Icons**: Lucide React
- **API Client**: Axios

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.11+
- Node.js v18+ & npm

---

### 2. Backend Setup & Run

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create and activate a Python virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install backend dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run database migrations:
   ```bash
   alembic upgrade head
   ```

5. Run unit tests to verify setup:
   ```bash
   pytest -v
   ```

6. Start the FastAPI development server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   - API Server: `http://localhost:8000`
   - Interactive Swagger API Documentation: `http://localhost:8000/docs`
   - ReDoc Documentation: `http://localhost:8000/redoc`

---

### 3. Frontend Setup & Run

1. Open a new terminal and navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the Vite development server:
   ```bash
   npm run dev
   ```

4. Open your browser and navigate to:
   👉 **[http://localhost:3000](http://localhost:3000)**

---

## 📡 API Reference Overview

All API endpoints are prefixed with `/api/v1`:

### Authentication
- `POST /api/v1/auth/register`: Register user and receive JWT bearer token
- `POST /api/v1/auth/login`: Authenticate credentials and receive token
- `GET /api/v1/auth/me`: Get current authenticated user profile

### Categories
- `GET /api/v1/categories`: Retrieve all categories (auto-seeds defaults on first call)
- `POST /api/v1/categories`: Create custom category
- `PUT /api/v1/categories/{id}`: Update category name
- `DELETE /api/v1/categories/{id}`: Delete category (blocked if in use)

### Transactions
- `GET /api/v1/transactions`: Filtered, searched, and paginated transactions
- `POST /api/v1/transactions`: Record income or expense
- `GET /api/v1/transactions/{id}`: Get single transaction details
- `PUT /api/v1/transactions/{id}`: Update transaction
- `DELETE /api/v1/transactions/{id}`: Delete transaction

### Savings
- `GET /api/v1/savings/summary`: Current balance, initial savings, and totals
- `GET /api/v1/savings/history`: Chronological savings ledger
- `POST /api/v1/savings/initialize`: Establish initial savings balance
- `POST /api/v1/savings/deposit`: Record savings deposit
- `POST /api/v1/savings/withdraw`: Record savings withdrawal with overdraft check
- `PATCH /api/v1/savings/balance`: True-up current balance via delta adjustment

### Budgets
- `GET /api/v1/budgets`: Monthly budget summary and utilization percentages
- `POST /api/v1/budgets`: Create overall or category-specific budget
- `PUT /api/v1/budgets/{id}`: Update budget amount
- `DELETE /api/v1/budgets/{id}`: Delete budget

### Dashboard & Reports
- `GET /api/v1/dashboard/summary`: Income, expenses, savings, and balance cards
- `GET /api/v1/dashboard/category-breakdown`: Expense share per category for pie charts
- `GET /api/v1/dashboard/monthly-trends`: Past $N$ months comparison for bar charts
- `GET /api/v1/dashboard/savings-trends`: Running balance history for line charts
- `GET /api/v1/reports/monthly`: Monthly financial statement, savings rate, and daily spend

---

## 🧪 Testing

The backend test suite is located in `backend/tests/` and uses in-memory SQLite isolation:

```bash
cd backend
pytest -v
```

**Test Coverage Summary**:
- User registration, duplicate email rejection, and input validation
- Argon2 password hashing and verification
- JWT generation and authorization checks
- User data isolation across all endpoints
- Category auto-seeding, duplicate prevention, and deletion safeguards
- Income & expense creation, type checks, filtering, searching, and pagination
- Savings initialization, deposits, overdraft rejection, balance adjustments, and ledger calculations
- Overall and category budget utilization, 80% warning, and 100% exceeded triggers
- Dashboard summary and report calculations without double counting

---

## 📜 License
MIT License. Built as a resume-worthy personal finance project.

