# CredResolve - Expense Sharing & Settlement Platform

A robust expense-sharing application that enables groups to track shared expenses, maintain balances, and settle debts efficiently using smart settlement algorithms.

---

## 🏗️ Backend Architecture

### Technology Stack

- **Framework**: Flask (Python 3.9+)
- **Database**: SQLite with WAL mode for concurrency
- **Authentication**: JWT-based token authentication
- **Password Security**: bcrypt hashing with salt rounds

### Architecture Overview

The backend follows a **layered service-oriented architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────┐
│                     REST API Layer                      │
│              (Flask Blueprints/Routes)                  │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────┐
│                   Service Layer                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │
│  │   User   │ │  Group   │ │ Expense  │ │Settlement│    │
│  │ Service  │ │ Service  │ │ Service  │ │ Service  │    │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘    │
│       │             │             │             │       │
│  ┌────────────┐ ┌────────────────────────────────┐      │
│  │   Auth     │ │      Balance Service           │      │
│  │ Middleware │ │  (Smart Settlement Logic)      │      │
│  └────────────┘ └────────────────────────────────┘      │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────┐
│              Data Persistence Layer                     │
│                    (SQLite DB)                          │
└─────────────────────────────────────────────────────────┘
```

### Core Services

#### 1. **User Service** (`services/user_service.py`)
- User registration with bcrypt password hashing
- Email uniqueness validation
- User lookup and management
- Cross-group balance aggregation

#### 2. **Authentication Middleware** (`middleware/auth.py`)
- JWT token generation and validation
- Route protection with `@auth_required` decorator
- Token expiration handling (24-hour validity)
- User context injection into requests

#### 3. **Group Service** (`services/group_service.py`)
- Group creation and management
- Member management with validation
- Multi-user group operations
- Group membership verification

#### 4. **Expense Service** (`services/expense_service.py`)
- Support for three split types:
  - **EQUAL**: Split amount equally among participants
  - **EXACT**: Specify exact amounts for each participant
  - **PERCENTAGE**: Distribute based on percentage shares
- Automatic balance updates on expense creation
- Split validation and calculation
- Expense deletion with balance rollback

#### 5. **Balance Service** (`services/balance_service.py`)
**Core Features:**
- Real-time balance tracking between users
- Automatic debt netting and consolidation
- Simplified balance calculation using greedy algorithm
- Smart settlement support for indirect debt resolution

**Key Algorithms:**

a) **Balance Netting** (`update_balance`):
```
When User A owes User B:
  If User B already owes User A (reverse debt exists):
    → Net the debts and store only the difference
  Else:
    → Add to User A's debt to User B
```

b) **Simplified Balances** (`get_simplified_balances`):
```
Algorithm: Minimum Transaction Settlement
1. Calculate net balance for each user
2. Separate users into debtors (negative) and creditors (positive)
3. Sort both lists by amount (descending)
4. Greedily match largest debtor with largest creditor
5. Continue until all balances are settled

Result: Minimum number of transactions to settle all debts
```

c) **Smart Settlement** (`apply_smart_settlement`):
```
Purpose: Enable indirect settlements (e.g., User3 → User1 directly 
         instead of User3 → User2 → User1)

Algorithm:
1. Validate payer has negative net balance (owes money)
2. Validate recipient has positive net balance (is owed)
3. Reduce payer's debts proportionally across all creditors
4. Reduce recipient's credits proportionally across all debtors
5. Record settlement transaction for audit trail

Example:
  Before: User3 → User2: $1000, User2 → User1: $1000
  Settlement: User3 pays User1 $1000 (smart settle)
  After: All balances cleared (0 transactions remaining)
```

#### 6. **Settlement Service** (`services/settlement_service.py`)
- Settlement recording with audit trail
- Smart settlement validation using net balances
- Maximum settlement amount enforcement
- Historical settlement tracking per group/user
- Remaining balance calculation after settlement

### Database Schema

```sql
-- Users table
CREATE TABLE users (
    id TEXT PRIMARY KEY,              -- UUID
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Groups table
CREATE TABLE groups (
    id TEXT PRIMARY KEY,              -- UUID
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    created_by TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Group membership (many-to-many)
CREATE TABLE group_members (
    group_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (group_id, user_id)
);

-- Expenses
CREATE TABLE expenses (
    id TEXT PRIMARY KEY,              -- UUID
    group_id TEXT NOT NULL,
    description TEXT NOT NULL,
    total_amount REAL NOT NULL,
    paid_by TEXT NOT NULL,
    split_type TEXT NOT NULL,         -- EQUAL, EXACT, PERCENTAGE
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Expense splits (normalized)
CREATE TABLE expense_splits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    expense_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    amount REAL,                      -- For EXACT splits
    percentage REAL                   -- For PERCENTAGE splits
);

-- Balances (denormalized for performance)
CREATE TABLE balances (
    group_id TEXT NOT NULL,
    from_user_id TEXT NOT NULL,       -- Debtor
    to_user_id TEXT NOT NULL,         -- Creditor
    amount REAL NOT NULL,
    PRIMARY KEY (group_id, from_user_id, to_user_id)
);

-- Settlements (audit trail)
CREATE TABLE settlements (
    id TEXT PRIMARY KEY,              -- UUID
    group_id TEXT NOT NULL,
    from_user_id TEXT NOT NULL,       -- Payer
    to_user_id TEXT NOT NULL,         -- Recipient
    amount REAL NOT NULL,
    settled_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_expenses_group ON expenses(group_id);
CREATE INDEX idx_splits_expense ON expense_splits(expense_id);
CREATE INDEX idx_settlements_group ON settlements(group_id);
CREATE INDEX idx_balances_group ON balances(group_id);
```

### API Endpoints

#### Authentication Routes (`/api/auth`)
```
POST   /auth/register          Register new user
POST   /auth/login             Login and get JWT token
GET    /auth/me                Get current user info (protected)
```

#### User Routes (`/api/users`)
```
GET    /users                  Get all users (protected)
GET    /users/:id              Get user by ID (protected)
POST   /users                  Create user (protected)
GET    /users/:id/balances     Get user's cross-group balances (protected)
```

#### Group Routes (`/api/groups`)
```
GET    /groups                           Get all groups (protected)
GET    /groups/:id                       Get group details (protected)
POST   /groups                           Create group (protected)
POST   /groups/:id/members               Add member to group (protected)
GET    /groups/:id/expenses              Get group expenses (protected)
GET    /groups/:id/balances              Get detailed balances (protected)
GET    /groups/:id/balances/simplified   Get simplified balances (protected)
```

#### Expense Routes (`/api/expenses`)
```
POST   /expenses               Create expense (protected)
GET    /expenses/:id           Get expense details (protected)
DELETE /expenses/:id           Delete expense (protected)
```

#### Settlement Routes (`/api/settlements`)
```
POST   /settlements                  Record settlement (protected)
GET    /settlements/:id              Get settlement details (protected)
GET    /settlements/groups/:id       Get group settlements (protected)
```

### Key Design Decisions

#### 1. **Denormalized Balance Table**
**Why**: Performance optimization for frequent balance queries
- Avoids complex JOINs and aggregations across expenses
- O(1) lookup for user-to-user balances
- Updated atomically with expense operations

**Trade-off**: Storage overhead vs query performance (query performance wins for read-heavy workload)

#### 2. **JWT Authentication over Session**
**Why**: Stateless authentication for scalability
- No server-side session storage required
- Easy horizontal scaling
- Per-tab isolation using sessionStorage on client

#### 3. **Service Layer Pattern**
**Why**: Separation of concerns and testability
- Business logic isolated from HTTP layer
- Services are reusable across different routes
- Easy to mock for unit testing
- Single responsibility principle

#### 4. **Smart Settlement Algorithm**
**Why**: Optimize user experience for complex debt chains
- Reduces number of real-world transactions
- More intuitive for users (A can pay C directly)
- Maintains mathematical correctness of balances
- Provides audit trail for all settlements

#### 5. **SQLite with WAL Mode**
**Why**: Balance between simplicity and concurrency
- No separate database server needed
- WAL mode allows concurrent reads during writes
- Sufficient for small-to-medium scale deployment
- Easy backup and migration

### Error Handling Strategy

```python
# Consistent error response format
{
    "error": {
        "code": "ERROR_CODE",
        "message": "Human-readable message"
    }
}

# HTTP Status Codes:
# 400 - Validation errors, business rule violations
# 401 - Authentication required
# 404 - Resource not found
# 500 - Unexpected server errors
```

### Security Features

1. **Password Security**: bcrypt with automatic salt generation (12 rounds)
2. **SQL Injection Prevention**: Parameterized queries throughout
3. **Authentication**: JWT tokens with expiration
4. **Authorization**: Route-level protection with middleware
5. **Input Validation**: Type checking and boundary validation in services

---

## 🎨 Frontend Overview

**Technology**: React 19 + TypeScript + Vite + Tailwind CSS

**Architecture**: Component-based SPA with React Router for navigation

**Key Features**:
- Dashboard with cross-group balance aggregation
- Group management with expense tracking
- Three balance views: Detailed, All Balances, Simplified
- Smart settlement UI with pre-filled modals
- Real-time balance updates after operations

**State Management**: React hooks (useState, useEffect) with API service layer

---

## 🚀 Setup & Execution

### Prerequisites
- Python 3.9+
- Node.js 18+
- pip and npm

### Backend Setup

```bash
cd server

# Install dependencies
pip install -r requirements.txt

# Start server (runs on http://localhost:3000)
python app.py
```

**Configuration**:
- Database: `server/data/app.db` (auto-created)
- JWT Secret: Set `JWT_SECRET` in environment or defaults to secure random
- API Port: 3000 (configurable via `PORT` environment variable)

### Frontend Setup

```bash
cd client

# Install dependencies
npm install

# Start development server (runs on http://localhost:5173)
npm run dev

# Build for production
npm run build
```

**Configuration**:
- API Base URL: `VITE_API_BASE_URL` environment variable or defaults to `http://localhost:3000/api`

### Quick Start (Full Stack)

**Terminal 1 - Backend**:
```bash
cd server && python app.py
```

**Terminal 2 - Frontend**:
```bash
cd client && npm run dev
```

Access application at `http://localhost:5173`

### Default Test Flow

1. **Register Users**: Create 3 users (user1@example.com, user2@example.com, user3@example.com)
2. **Create Group**: Login as user1, create a group, add all members
3. **Add Expenses**: 
   - User1 pays $1000 (split equally)
   - User2 pays $500 (split equally)
4. **View Balances**: Check "Simplified" tab for minimum transactions
5. **Smart Settle**: Click "Smart Settle" to pay optimal path
6. **Verify**: Check all dashboards show correct balances

---

## 📊 Performance Characteristics

| Operation | Complexity | Notes |
|-----------|-----------|-------|
| Balance Lookup | O(1) | Direct table lookup |
| Simplified Balance Calc | O(n log n) | Sorting dominant factor |
| Expense Creation | O(m) | m = number of splits |
| Smart Settlement | O(b) | b = number of existing balances |
| User Balance Aggregate | O(g) | g = number of groups |

---

## 🔮 Future Enhancements

### Backend
- [ ] PostgreSQL migration for production scalability
- [ ] Redis caching for balance queries
- [ ] Webhook support for external integrations
- [ ] GraphQL API layer
- [ ] Multi-currency support with exchange rates
- [ ] Recurring expense scheduling
- [ ] Balance history and snapshots

### Algorithms
- [ ] Alternative settlement algorithms (minimum cash flow vs balanced transactions)
- [ ] Priority-based debt settlement
- [ ] Partial settlement suggestions

### DevOps
- [ ] Docker containerization
- [ ] CI/CD pipeline with automated tests
- [ ] Horizontal scaling with load balancer
- [ ] Database replication and sharding

---

## 📝 License

This project is created as an assignment task for CredResolve.

---

## 👨‍💻 Development Notes

### Testing Settlement Algorithm

```bash
# Clear database for fresh testing
cd server
rm -f data/app.db

# Restart server
python app.py
```

### Database Inspection

```bash
cd server/data
sqlite3 app.db

# Useful queries:
SELECT * FROM balances;
SELECT * FROM settlements ORDER BY settled_at DESC;
SELECT * FROM expenses ORDER BY created_at DESC;
```

### Debug Mode

Set `FLASK_ENV=development` for auto-reload and detailed error pages.

---
