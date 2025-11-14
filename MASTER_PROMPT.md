# Canopy - Master Prompt for Recreation

This document provides a comprehensive guide to recreate the Canopy application from scratch. Use this as a master prompt for AI assistants or developers.

## Project Overview

**Canopy** is a self-hosted personal finance & investment dashboard that merges portfolio analytics, budgeting, and transaction tracking into one unified platform. It is designed to run on a Raspberry Pi cluster with a lean footprint, storing all data locally without cloud dependencies.

### Core Objectives
- Combine portfolio, budgeting, and net-worth views into a single dashboard
- Store all data locally — no cloud dependencies
- Support multi-currency (CAD, USD, BRL, EUR, GBP) assets
- Allow easy CSV/OFX imports for banks and brokerages
- Run lean — optimized for Raspberry Pi hardware
- Be modular so other developers can fork and extend

### Design Philosophy & Rationale

**Why Self-Hosted?**
- **Privacy First:** Financial data is sensitive. Self-hosting ensures complete control over where data is stored and who has access.
- **No Vendor Lock-in:** Avoid dependency on third-party services that may change pricing, features, or discontinue service.
- **Cost Efficiency:** Run on existing hardware (Raspberry Pi) without subscription fees.
- **Data Ownership:** Users own their data completely, enabling export and migration at any time.

**Why Raspberry Pi Optimized?**
- **Accessibility:** Raspberry Pi is affordable and widely available, making self-hosting accessible to more users.
- **Low Power Consumption:** Can run 24/7 without significant electricity costs.
- **Educational Value:** Encourages learning about self-hosting, Linux, and system administration.
- **Edge Computing:** Data processing happens locally, reducing latency and bandwidth usage.

**Why Multi-Currency Support?**
- **Global Users:** Many users have assets and transactions in multiple currencies.
- **Accurate Reporting:** Convert all transactions to a single display currency for meaningful analysis.
- **Investment Tracking:** Portfolio assets are often denominated in different currencies.
- **Future-Proofing:** Supports international expansion and diverse user bases.

**Why Modular Architecture?**
- **Extensibility:** Easy to add new features without breaking existing functionality.
- **Maintainability:** Clear separation of concerns makes code easier to understand and modify.
- **Community Contribution:** Modular design allows community members to contribute specific features.
- **Testing:** Isolated modules are easier to test independently.

### MVP Features Implemented
- 💰 Transaction tracking with categories
- 🔄 Multi-currency FX conversions with display currency toggle
- 📊 Dashboard with charts and statistics
- 🌙 Dark mode support
- 🎨 Modern Monarch Money-inspired UI

---

## Technology Stack

### Backend
- **Framework**: FastAPI 0.104.1
  - **Why FastAPI?** Async/await support for high performance, automatic OpenAPI/Swagger docs, type hints for better code quality, and excellent Python 3.10+ support. Perfect for building modern APIs quickly.
- **ASGI Server**: Uvicorn[standard] 0.24.0
  - **Why Uvicorn?** Fast ASGI server built on uvloop for better performance than traditional WSGI servers. The `[standard]` extras include better performance and websocket support.
- **Database**: PostgreSQL (via SQLAlchemy 2.0.23, psycopg[binary] 3.1.18)
  - **Why PostgreSQL?** Robust, ACID-compliant, excellent JSON support, and strong performance. Industry standard for financial applications.
  - **Why SQLAlchemy?** Powerful ORM with async support, database-agnostic abstractions, and excellent migration tools.
  - **Why psycopg[binary]?** Pre-compiled binaries avoid compilation issues on various platforms, faster setup.
- **Migrations**: Alembic 1.12.1
  - **Why Alembic?** SQLAlchemy's official migration tool, integrates seamlessly, supports version control for schema changes.
- **Validation**: Pydantic 2.5.0, pydantic-settings 2.1.0
  - **Why Pydantic v2?** Performance improvements, better type validation, and integration with FastAPI. Used for both request/response validation and settings management.
- **Auth**: python-jose[cryptography] 3.3.0, passlib[bcrypt] 1.7.4
  - **Why JOSE?** Industry-standard JWT implementation for secure token-based authentication.
  - **Why bcrypt?** Strong password hashing algorithm resistant to brute-force attacks.
- **Task Queue**: Celery 5.3.4
  - **Why Celery?** Handles background tasks (CSV imports, report generation) without blocking the API. Essential for long-running operations.
- **Cache**: Redis 5.0.1
  - **Why Redis?** Fast in-memory cache for frequently accessed data (exchange rates, user sessions). Also used as Celery broker.
- **HTTP Client**: httpx 0.25.2
  - **Why httpx?** Modern async HTTP client, better than requests for async code, useful for fetching exchange rates or external APIs.
- **Testing**: pytest 7.4.3, pytest-asyncio 0.21.1
  - **Why pytest?** Industry standard Python testing framework with excellent fixtures and async support.
- **Environment**: python-dotenv 1.0.0
  - **Why dotenv?** Standard way to manage environment variables in development, keeps secrets out of code.

### Frontend
- **Framework**: Next.js 14.0.4
  - **Why Next.js?** Server-side rendering for better SEO and performance, file-based routing for simplicity, built-in optimizations (image, font, script), and excellent developer experience. Perfect for dashboard applications.
- **UI Library**: React 18.2.0
  - **Why React?** Most popular UI library, excellent ecosystem, component reusability, and strong TypeScript support.
- **Styling**: Tailwind CSS 3.3.6
  - **Why Tailwind?** Utility-first CSS enables rapid UI development without context switching, consistent design system, smaller bundle sizes through purging, and excellent dark mode support via class strategy.
- **Charts**: Recharts 2.10.3
  - **Why Recharts?** React-native charting library, declarative API, responsive by default, and composable components. Better than D3 for React applications.
- **Icons**: Lucide React 0.294.0
  - **Why Lucide?** Clean, consistent icon set, tree-shakeable (only import used icons), TypeScript support, and good variety for financial apps.
- **Date Utils**: date-fns 2.30.0
  - **Why date-fns?** Immutable, functional API, tree-shakeable, better than Moment.js (smaller bundle), and excellent TypeScript support.
- **Language**: TypeScript 5.3.3
  - **Why TypeScript?** Type safety catches errors at compile time, better IDE support, self-documenting code, and reduces runtime errors. Essential for maintainable frontend code.

### Infrastructure
- **Containerization**: Docker & Docker Compose
- **Orchestration**: Kubernetes (k8s manifests included)
- **Database**: PostgreSQL
- **Cache**: Redis

---

## Project Structure

```
canopy/
├── backend/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── transactions.py      # Transaction CRUD endpoints
│   │   └── currency.py          # Currency conversion endpoints
│   ├── app/
│   │   ├── __init__.py
│   │   └── server.py            # FastAPI app entry point
│   ├── models/
│   │   ├── __init__.py
│   │   ├── transaction.py        # Transaction Pydantic models
│   │   └── currency.py          # Currency models & conversion logic
│   ├── ingest/                  # CSV/OFX import handlers (future)
│   └── requirements.txt
├── frontend/
│   ├── components/
│   │   ├── Sidebar.tsx          # Navigation sidebar
│   │   ├── StatCard.tsx        # Reusable stat card component
│   │   ├── CurrencySelector.tsx # Currency dropdown selector
│   │   └── DarkModeToggle.tsx  # Dark mode toggle button
│   ├── pages/
│   │   ├── _app.tsx            # Next.js app wrapper
│   │   ├── index.tsx           # Dashboard page
│   │   ├── transactions.tsx    # Transactions management page
│   │   ├── portfolio.tsx       # Portfolio page (placeholder)
│   │   ├── accounts.tsx       # Accounts page (placeholder)
│   │   └── settings.tsx       # Settings page
│   ├── styles/
│   │   └── globals.css         # Global styles & Tailwind components
│   ├── utils/
│   │   └── currency.ts         # Currency formatting & conversion utilities
│   ├── package.json
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── next.config.js
├── k8s/
│   ├── deploy.yaml
│   ├── service.yaml
│   └── ingress.yaml
└── README.md
```

---

## Backend Implementation

### 1. FastAPI Server Setup (`backend/app/server.py`)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import sys

# Add backend directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.api import transactions, currency

load_dotenv()

app = FastAPI(
    title="Canopy API",
    description="Privacy-first personal finance and investment cockpit",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(transactions.router)
app.include_router(currency.router)

@app.get("/v1/health")
async def health_check():
    return {
        "status": "healthy",
        "environment": os.getenv("ENVIRONMENT", "development"),
    }

@app.get("/")
async def root():
    return {"message": "Canopy API", "version": "0.1.0"}
```

**Key Points:**
- CORS enabled for frontend (localhost:3000)
- Path manipulation to allow imports from backend directory
- Health check endpoint for monitoring
- Router inclusion pattern for modular API

**Design Rationale:**

**Why CORS Middleware?**
- **Browser Security:** Browsers enforce Same-Origin Policy. Without CORS, the frontend (localhost:3000) cannot call the backend API (localhost:8000) due to different ports.
- **Development vs Production:** Currently allows localhost origins. In production, this should be restricted to specific domains for security.
- **Credentials:** `allow_credentials=True` enables cookies/auth headers to be sent cross-origin when authentication is added.

**Why Path Manipulation?**
- **Import Resolution:** Python needs to find the `backend` module. Adding parent directory to `sys.path` allows absolute imports (`from backend.api import ...`) to work regardless of where uvicorn is run from.
- **Alternative Approaches:** Could use relative imports or PYTHONPATH environment variable, but explicit path manipulation is more predictable.

**Why Health Check Endpoint?**
- **Monitoring:** Kubernetes, load balancers, and monitoring tools can check `/v1/health` to determine if the service is running.
- **Status Verification:** Returns environment info for debugging and deployment verification.
- **Best Practice:** Standard pattern for microservices and containerized applications.

**Why Router Pattern?**
- **Separation of Concerns:** Each router handles a specific domain (transactions, currency) making code easier to maintain.
- **Scalability:** Easy to add new routers without modifying main server file.
- **Testing:** Routers can be tested independently.
- **Team Collaboration:** Different developers can work on different routers without conflicts.

### 2. Transaction Models (`backend/models/transaction.py`)

```python
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from enum import Enum

class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"

class Transaction(BaseModel):
    id: Optional[int] = None
    description: str
    amount: float
    currency: str = "USD"
    type: TransactionType
    category: Optional[str] = None
    date: datetime
    account: Optional[str] = None

class TransactionCreate(BaseModel):
    description: str
    amount: float
    currency: str = "USD"
    type: TransactionType
    category: Optional[str] = None
    date: Optional[datetime] = None
    account: Optional[str] = None
```

### 3. Transaction API (`backend/api/transactions.py`)

**Endpoints:**
- `GET /v1/transactions/` - List all transactions (optional `currency` query param for conversion)
- `GET /v1/transactions/{transaction_id}` - Get specific transaction
- `POST /v1/transactions/` - Create new transaction
- `DELETE /v1/transactions/{transaction_id}` - Delete transaction

**Current Implementation:**
- Uses in-memory storage (List[Transaction])
- Global `next_id` counter for ID generation
- Optional currency conversion on GET all

**Why In-Memory Storage Initially?**
- **Rapid Prototyping:** MVP doesn't require persistence. Allows fast iteration without database setup.
- **Simplicity:** No database migrations, connection pooling, or schema management needed initially.
- **Testing:** Easy to reset state by restarting the server.
- **Migration Path:** Code structure supports easy migration to database later (models are already Pydantic models compatible with SQLAlchemy).

**Why Global Counter for IDs?**
- **Simplicity:** No need for database sequences or UUID generation in MVP.
- **Migration-Friendly:** When moving to database, can use auto-incrementing primary keys or UUIDs.
- **Temporary Solution:** Will be replaced with proper database primary keys.

**Why Optional Currency Conversion?**
- **Performance:** Don't convert if not needed (user viewing in original currency).
- **Flexibility:** Client can request specific currency when needed.
- **API Design:** Query parameter pattern allows same endpoint to serve multiple use cases.

**Key Logic:**
```python
# Currency conversion example
if currency:
    converted_transactions = []
    for tx in transactions_db:
        converted_amount = convert_currency(tx.amount, tx.currency, currency.upper())
        # Use model_dump() for Pydantic v2, fallback to dict() for v1
        tx_dict = tx.model_dump() if hasattr(tx, 'model_dump') else tx.dict()
        converted_tx = Transaction(**tx_dict, amount=converted_amount, currency=currency.upper())
        converted_transactions.append(converted_tx)
    return converted_transactions
```

**Why model_dump() with Fallback?**
- **Pydantic v2 Compatibility:** `dict()` was deprecated in Pydantic v2, replaced with `model_dump()`.
- **Backward Compatibility:** Fallback ensures code works with both Pydantic v1 and v2.
- **Future-Proofing:** Code will work as Pydantic evolves.
- **Best Practice:** Check for method existence rather than version checking.

### 4. Currency Models (`backend/models/currency.py`)

**Features:**
- Mock exchange rates for USD, CAD, BRL, EUR, GBP
- Currency conversion function
- Supported currencies list

**Exchange Rates Structure:**
```python
DEFAULT_EXCHANGE_RATES = {
    "USD": {"USD": 1.0, "CAD": 1.35, "BRL": 5.10, "EUR": 0.92, "GBP": 0.79},
    "CAD": {"USD": 0.74, "CAD": 1.0, "BRL": 3.78, "EUR": 0.68, "GBP": 0.59},
    # ... etc
}
```

**Conversion Function:**
```python
def convert_currency(amount: float, from_currency: str, to_currency: str) -> float:
    if from_currency == to_currency:
        return amount
    rates = DEFAULT_EXCHANGE_RATES.get(from_currency, {})
    rate = rates.get(to_currency, 1.0)
    return amount * rate
```

**Why Mock Exchange Rates Initially?**
- **Development Speed:** No external API dependencies during development.
- **Testing:** Predictable rates make testing easier and reproducible.
- **Offline Development:** Works without internet connection.
- **Cost:** Avoids API rate limits and costs during development.
- **Migration Path:** Structure supports easy swap to real API (exchangerate-api.io, Fixer.io, etc.) later.

**Why USD as Base Currency?**
- **Common Standard:** USD is widely used as base currency in financial markets.
- **User Base:** Many users think in USD terms.
- **Flexibility:** Can easily add more base currencies or use EUR/CAD as base if needed.

### 5. Currency API (`backend/api/currency.py`)

**Endpoints:**
- `GET /v1/currency/supported` - Get list of supported currencies
- `GET /v1/currency/rates?base_currency=USD` - Get exchange rates
- `GET /v1/currency/convert?amount=100&from_currency=USD&to_currency=CAD` - Convert amount

---

## Frontend Implementation

### 1. Next.js Configuration

**`frontend/next.config.js`:**
```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
}

module.exports = nextConfig
```

**`frontend/tsconfig.json`:**
Standard Next.js TypeScript configuration with path aliases:
```json
{
  "compilerOptions": {
    "target": "es5",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [
      {
        "name": "next"
      }
    ],
    "paths": {
      "@/*": ["./*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

### 2. Tailwind Configuration (`frontend/tailwind.config.js`)

**Key Features:**
- Dark mode: `class` strategy
- Custom primary color palette (blue scale)
- Inter font family
- Content paths for JIT compilation

```javascript
module.exports = {
  darkMode: 'class',
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          // ... through 900
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
```

### 3. Global Styles (`frontend/styles/globals.css`)

**Custom Components:**
- `.card` - Card container with dark mode support
- `.card-hover` - Hover effects for cards
- `.btn-primary` - Primary button with gradient
- `.btn-secondary` - Secondary button
- `.input-modern` - Modern input styling

```css
@layer components {
  .card {
    @apply bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700;
  }
  
  .btn-primary {
    @apply bg-gradient-to-r from-primary-600 to-primary-700 text-white font-medium px-6 py-3 rounded-xl shadow-md hover:shadow-lg transition-all duration-200;
  }
  
  .input-modern {
    @apply w-full px-4 py-3 border border-gray-200 dark:border-gray-700 rounded-xl focus:ring-2 focus:ring-primary-500 bg-white dark:bg-gray-800;
  }
}
```

### 4. Core Components

#### Sidebar (`frontend/components/Sidebar.tsx`)

**Features:**
- Fixed left sidebar (64 width, `w-64`)
- Navigation links with active state highlighting
- Dark mode toggle integration
- Gradient branding header
- Privacy footer message

**Navigation Items:**
- Dashboard (`/`)
- Transactions (`/transactions`)
- Portfolio (`/portfolio`)
- Accounts (`/accounts`)
- Settings (`/settings`)

**Active State Logic:**
```typescript
const isActive = router.pathname === item.href
// Apply active styles: bg-primary-600 text-white shadow-lg
```

#### DarkModeToggle (`frontend/components/DarkModeToggle.tsx`)

**Features:**
- localStorage persistence
- System preference detection
- Prevents hydration mismatch
- Toggles `dark` class on `document.documentElement`

**Why localStorage Persistence?**
- **User Experience:** Remembers user preference across sessions.
- **Consistency:** Same theme on every visit unless user changes it.
- **Respects Choice:** User's explicit selection takes precedence over system preference.

**Why System Preference Detection?**
- **First Visit:** New users get sensible default based on their OS setting.
- **Accessibility:** Users with light sensitivity get appropriate default.
- **Modern UX:** Expected behavior in modern applications.

**Why Prevent Hydration Mismatch?**
- **SSR Issue:** Server doesn't know user's preference, would render different HTML than client.
- **React Error:** Mismatches cause React warnings and potential UI glitches.
- **Solution:** Render placeholder until client-side JavaScript loads, then apply preference.

**Why Document.documentElement?**
- **Global Scope:** Dark mode affects entire page, not just React components.
- **Tailwind Integration:** Tailwind's `dark:` variants check for `dark` class on `<html>` element.
- **Performance:** Single DOM manipulation affects all elements, more efficient than per-component checks.

**Key Implementation:**
```typescript
useEffect(() => {
  setMounted(true)
  const stored = localStorage.getItem('darkMode')
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
  const isDark = stored !== null ? stored === 'true' : prefersDark
  
  setDarkMode(isDark)
  if (isDark) {
    document.documentElement.classList.add('dark')
  }
}, [])
```

#### StatCard (`frontend/components/StatCard.tsx`)

**Props:**
- `title`: Stat label
- `value`: Stat value (formatted string)
- `change`: Optional change indicator
- `changeType`: 'positive' | 'negative' | 'neutral'
- `icon`: Lucide icon component
- `gradient`: Tailwind gradient class

**Visual Features:**
- Gradient background decoration
- Icon badge
- Change indicator badge with color coding

#### CurrencySelector (`frontend/components/CurrencySelector.tsx`)

**Features:**
- Dropdown with supported currencies
- Currency code and symbol display
- Dark mode styling
- Callback on change

**Supported Currencies:**
- USD ($), CAD (C$), BRL (R$), EUR (€), GBP (£)

### 5. Utility Functions (`frontend/utils/currency.ts`)

**Functions:**
- `formatCurrency(amount, currencyCode)` - Format with Intl.NumberFormat
- `formatCurrencyCompact(amount, currencyCode)` - Compact notation
- `getCurrencySymbol(currencyCode)` - Get currency symbol
- `convertCurrency(amount, fromCurrency, toCurrency)` - API call for conversion

**Implementation:**
```typescript
export async function convertCurrency(
  amount: number,
  fromCurrency: string,
  toCurrency: string
): Promise<number> {
  if (fromCurrency === toCurrency) return amount
  
  const response = await fetch(
    `http://localhost:8000/v1/currency/convert?amount=${amount}&from_currency=${fromCurrency}&to_currency=${toCurrency}`
  )
  const data = await response.json()
  return data.converted_amount
}
```

### 6. Pages

#### Dashboard (`frontend/pages/index.tsx`)

**Features:**
- Stat cards (Total Income, Total Expenses, Net Cash Flow, Spending)
- Cash flow area chart (income vs expenses over time)
- Spending by category pie chart
- Recent transactions list
- Currency selector and conversion toggle
- Dark mode support

**State Management:**
- `transactions`: Transaction list
- `displayCurrency`: Selected display currency
- `showConverted`: Toggle to show/hide converted amounts
- `convertedAmounts`: Map of transaction ID to converted amount
- `isDarkMode`: Dark mode state (for chart tooltips)

**Key Logic:**
```typescript
// Convert all amounts when currency changes
useEffect(() => {
  if (transactions.length > 0 && showConverted) {
    convertAllAmounts()
  }
}, [transactions, displayCurrency, showConverted])

// Display logic: show original + converted if different currency
const converted = getConvertedAmount(tx)
const displayAmount = converted ?? tx.amount
```

**Charts:**
- AreaChart: Income (green) vs Expenses (red) over time
- PieChart: Spending breakdown by category with color coding

#### Transactions Page (`frontend/pages/transactions.tsx`)

**Features:**
- Transaction list with filtering
- Add transaction form (collapsible)
- Delete transaction functionality
- Currency conversion display
- Transaction type icons (TrendingUp, TrendingDown, ArrowLeftRight)
- Summary cards (Total Income, Total Expenses, Net)

**Form Fields:**
- Description (text)
- Amount (number)
- Currency (dropdown)
- Type (income/expense/transfer)
- Category (text, optional)
- Account (text, optional)
- Date (date picker)

**Transaction Display:**
- Shows original amount in original currency
- Shows converted amount in display currency (if different)
- Format: "$100.00 (from USD: $135.00 CAD)" when converted

#### Portfolio Page (`frontend/pages/portfolio.tsx`)

**Status:** Placeholder page

**Features:**
- Stat cards for portfolio metrics
- Coming soon message
- Dark mode support

#### Accounts Page (`frontend/pages/accounts.tsx`)

**Status:** Placeholder page

**Features:**
- Account cards (Checking, Credit Card, Savings)
- Add Account button (disabled)
- Coming soon message
- Dark mode support

#### Settings Page (`frontend/pages/settings.tsx`)

**Features:**
- Currency selector
- Dark mode toggle
- Profile settings (placeholder, disabled)
- Notification settings (placeholder, disabled)
- Privacy & Security settings (placeholder)

---

## UI/UX Design System

### Design Inspiration
Monarch Money-style modern, clean interface

### Color Palette

**Primary Colors:**
- Primary 50-900: Blue scale (#f0f9ff to #0c4a9e)
- Used for buttons, accents, active states

**Semantic Colors:**
- Green: Income, positive changes (#10b981)
- Red: Expenses, negative changes (#ef4444)
- Gray: Neutral elements, backgrounds

**Dark Mode:**
- Background: gray-950
- Cards: gray-800
- Text: gray-100/gray-300
- Borders: gray-700

### Typography
- Font: Inter (Google Fonts)
- Weights: 300, 400, 500, 600, 700, 800
- Headings: Bold, larger sizes
- Body: Regular weight

### Spacing & Layout
- Sidebar: Fixed, 64 width units (`w-64` = 256px)
- Main content: `ml-64` to account for sidebar
- Card padding: `p-6` (24px)
- Border radius: `rounded-xl` (12px) or `rounded-2xl` (16px)
- Gap between elements: `gap-4`, `gap-6`

### Components Style Guide

**Cards:**
- White background (dark: gray-800)
- Rounded corners (rounded-2xl)
- Subtle shadow (shadow-sm)
- Border (gray-100/gray-700)

**Buttons:**
- Primary: Gradient background, white text, rounded-xl
- Secondary: White/gray background, border, rounded-xl
- Hover effects: Shadow increase, slight scale

**Inputs:**
- Rounded-xl
- Border focus ring (primary-500)
- Dark mode compatible

**Icons:**
- Lucide React icons
- Size: 20px standard, 16px small, 24px large
- Color matches text color

---

## Setup Instructions

### Prerequisites
- Python 3.10+ (with pyenv recommended)
- Node.js 18+ and npm
- Docker and Docker Compose
- PostgreSQL (via Docker)
- Redis (via Docker)

### Backend Setup

1. **Create Python virtual environment:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
# OR with pyenv:
pyenv local canopy
pyenv virtualenv canopy
pyenv activate canopy
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Create `.env` file:**
```env
DATABASE_URL=postgresql://user:password@localhost:5432/canopy
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key-here
DEBUG=True
ENVIRONMENT=development
ALLOWED_HOSTS=localhost,127.0.0.1
API_V1_PREFIX=/v1
```

4. **Start Docker services:**
```bash
docker compose up -d postgres redis
```

5. **Run migrations (when database is set up):**
```bash
alembic upgrade head
```

6. **Start backend server:**
```bash
cd backend
PYTHONPATH=/path/to/canopy/backend python3 -m uvicorn app.server:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

1. **Install dependencies:**
```bash
cd frontend
npm install
```

2. **Start development server:**
```bash
npm run dev
```

3. **Access application:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Quick Start Script

Create `run-local.sh`:
```bash
#!/bin/bash
set -e

# Start Docker services
docker compose up -d

# Backend setup
cd backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    cp .env.example .env
fi

# Frontend setup
cd ../frontend
npm install

echo "Setup complete! Start services:"
echo "Backend: cd backend && source venv/bin/activate && PYTHONPATH=.. python3 -m uvicorn app.server:app --reload"
echo "Frontend: cd frontend && npm run dev"
```

---

## Kubernetes Deployment with Vault Secrets Management

### Overview

Canopy is deployed to a Raspberry Pi k3s cluster (eldertree) using Kubernetes manifests. **ALL secrets are managed through Vault** and automatically synced to Kubernetes via External Secrets Operator. This ensures no hardcoded secrets in deployment files and centralized secret management.

### Prerequisites

- k3s cluster running (eldertree control plane)
- Vault deployed and accessible
- External Secrets Operator installed and configured
- ClusterSecretStore configured for Vault
- kubectl configured with `~/.kube/config-eldertree`

### Vault Secrets Configuration

**All Canopy secrets are stored in Vault at these paths:**

- `secret/canopy/postgres` - PostgreSQL password
- `secret/canopy/app` - Application secret key
- `secret/canopy/database` - Complete database URL

**Setting Secrets in Vault:**

```bash
# Get Vault pod
VAULT_POD=$(kubectl get pods -n vault -l app.kubernetes.io/name=vault -o jsonpath='{.items[0].metadata.name}')

# Set PostgreSQL password
kubectl exec -n vault $VAULT_POD -- sh -c "export VAULT_ADDR=http://127.0.0.1:8200 && export VAULT_TOKEN=root && vault kv put secret/canopy/postgres password=\$(python3 -c 'import secrets; print(secrets.token_urlsafe(16))')"

# Set application secret key
kubectl exec -n vault $VAULT_POD -- sh -c "export VAULT_ADDR=http://127.0.0.1:8200 && export VAULT_TOKEN=root && vault kv put secret/canopy/app secret-key=\$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"

# Set database URL (use password from postgres secret)
POSTGRES_PWD=$(kubectl exec -n vault $VAULT_POD -- sh -c "export VAULT_ADDR=http://127.0.0.1:8200 && export VAULT_TOKEN=root && vault kv get -field=password secret/canopy/postgres")
kubectl exec -n vault $VAULT_POD -- sh -c "export VAULT_ADDR=http://127.0.0.1:8200 && export VAULT_TOKEN=root && vault kv put secret/canopy/database url=postgresql+psycopg://canopy:$POSTGRES_PWD@canopy-postgres:5432/canopy"
```

### ExternalSecret Resource

The ExternalSecret resource automatically syncs secrets from Vault to Kubernetes:

```yaml
# Located at: pi-fleet/clusters/eldertree/infrastructure/external-secrets/externalsecrets/canopy-secrets.yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: canopy-secrets
  namespace: canopy
spec:
  refreshInterval: 24h
  secretStoreRef:
    name: vault
    kind: ClusterSecretStore
  target:
    name: canopy-secrets
    creationPolicy: Owner
  data:
    - secretKey: postgres-password
      remoteRef:
        key: secret/canopy/postgres
        property: password
    - secretKey: secret-key
      remoteRef:
        key: secret/canopy/app
        property: secret-key
    - secretKey: database-url
      remoteRef:
        key: secret/canopy/database
        property: url
```

**Important:** This ExternalSecret is managed by Flux GitOps in the pi-fleet repository. It automatically syncs secrets every 24 hours.

### Kubernetes Deployment Configuration

**Deployment File:** `k8s/deploy.yaml`

**Key Features:**
- API deployment with 2 replicas
- Frontend deployment with 2 replicas
- PostgreSQL StatefulSet with persistent storage (10Gi)
- Redis deployment for caching
- All secrets referenced via `secretKeyRef` from `canopy-secrets`
- Resource limits configured for Raspberry Pi constraints

**Environment Variables from Secrets:**

```yaml
env:
  - name: DATABASE_URL
    valueFrom:
      secretKeyRef:
        name: canopy-secrets
        key: database-url
  - name: SECRET_KEY
    valueFrom:
      secretKeyRef:
        name: canopy-secrets
        key: secret-key
  - name: POSTGRES_PASSWORD  # For PostgreSQL container
    valueFrom:
      secretKeyRef:
        name: canopy-secrets
        key: postgres-password
```

### Deployment Steps

1. **Ensure Vault secrets are set** (see above)

2. **Verify ExternalSecret is syncing:**
```bash
kubectl get externalsecret canopy-secrets -n canopy
kubectl get secret canopy-secrets -n canopy
```

3. **Deploy application:**
```bash
export KUBECONFIG=~/.kube/config-eldertree
kubectl apply -f k8s/deploy.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
```

4. **Verify deployment:**
```bash
kubectl get pods -n canopy
kubectl get svc -n canopy
kubectl get ingress -n canopy
kubectl logs -f deployment/canopy-api -n canopy
```

### Ingress Configuration

**File:** `k8s/ingress.yaml`

- Host: `canopy.eldertree.local`
- TLS: Managed by cert-manager with self-signed certificates
- Paths:
  - `/api` → canopy-api service (port 8000)
  - `/` → canopy-frontend service (port 3000)

### Resource Requirements

**Per Replica:**
- API: 256Mi RAM, 250m CPU (limits: 512Mi, 500m)
- Frontend: 128Mi RAM, 100m CPU (limits: 256Mi, 200m)
- Redis: 64Mi RAM, 50m CPU (limits: 128Mi, 100m)
- PostgreSQL: 256Mi RAM, 250m CPU (limits: 512Mi, 500m)

**Total (2 API + 2 Frontend):**
- ~1.2Gi RAM
- ~1 CPU

### Security Best Practices

✅ **All secrets in Vault** - Single source of truth  
✅ **External Secrets Operator** - Automatic sync every 24 hours  
✅ **No hardcoded secrets** - All deployments use `secretKeyRef`  
✅ **Safe defaults** - Config files have development defaults only  
✅ **Production overrides** - Environment variables from secrets override defaults  

### Troubleshooting

**Secrets not syncing:**
```bash
# Check ExternalSecret status
kubectl describe externalsecret canopy-secrets -n canopy

# Check External Secrets Operator logs
kubectl logs -n external-secrets deployment/external-secrets

# Verify secrets exist in Vault
VAULT_POD=$(kubectl get pods -n vault -l app.kubernetes.io/name=vault -o jsonpath='{.items[0].metadata.name}')
kubectl exec -n vault $VAULT_POD -- sh -c "export VAULT_ADDR=http://127.0.0.1:8200 && export VAULT_TOKEN=root && vault kv list secret/canopy/"
```

**Pods failing to start:**
```bash
# Check pod logs
kubectl logs deployment/canopy-api -n canopy

# Check if secrets exist
kubectl get secret canopy-secrets -n canopy -o yaml

# Verify environment variables
kubectl exec deployment/canopy-api -n canopy -- env | grep -E "DATABASE_URL|SECRET_KEY"
```

**Database connection issues:**
```bash
# Verify PostgreSQL is running
kubectl get pods -n canopy | grep postgres

# Check PostgreSQL logs
kubectl logs statefulset/canopy-postgres -n canopy

# Test database connection from API pod
kubectl exec deployment/canopy-api -n canopy -- python3 -c "import os; print(os.getenv('DATABASE_URL'))"
```

### CI/CD Integration

Canopy uses GitHub Actions with a self-hosted runner on the Pi cluster. The workflow:
1. Builds Docker images
2. Pushes to GHCR (ghcr.io/raolivei/canopy-api:v1.0.0)
3. Applies Kubernetes manifests
4. Restarts deployments to pull latest images

**Important:** Secrets are NOT managed by CI/CD. They are set manually in Vault and synced automatically by External Secrets Operator.

---

## API Specifications

### Base URL
- Development: `http://localhost:8000`
- API Prefix: `/v1`

### Endpoints

#### Health Check
- `GET /v1/health`
- Response: `{"status": "healthy", "environment": "development"}`

#### Transactions

**List Transactions**
- `GET /v1/transactions/`
- Query Params:
  - `currency` (optional): Convert all amounts to this currency
- Response: `Transaction[]`

**Get Transaction**
- `GET /v1/transactions/{transaction_id}`
- Response: `Transaction`

**Create Transaction**
- `POST /v1/transactions/`
- Body: `TransactionCreate`
- Response: `Transaction`

**Delete Transaction**
- `DELETE /v1/transactions/{transaction_id}`
- Response: `{"message": "Transaction deleted"}`

#### Currency

**Get Supported Currencies**
- `GET /v1/currency/supported`
- Response: `{"currencies": ["USD", "CAD", ...], "default": "USD"}`

**Get Exchange Rates**
- `GET /v1/currency/rates?base_currency=USD`
- Response: `{"base_currency": "USD", "rates": {...}, "date": "..."}`

**Convert Amount**
- `GET /v1/currency/convert?amount=100&from_currency=USD&to_currency=CAD`
- Response: `{"original_amount": 100, "original_currency": "USD", "converted_amount": 135, "converted_currency": "CAD", "exchange_rate": 1.35}`

### Data Models

**Transaction:**
```json
{
  "id": 1,
  "description": "Groceries",
  "amount": 150.50,
  "currency": "USD",
  "type": "expense",
  "category": "Food",
  "date": "2024-01-15T10:30:00",
  "account": "Checking"
}
```

**TransactionCreate:**
```json
{
  "description": "Salary",
  "amount": 5000.00,
  "currency": "USD",
  "type": "income",
  "category": "Salary",
  "date": "2024-01-15T10:30:00",
  "account": "Checking"
}
```

---

## Key Implementation Details

### Currency Conversion Flow

1. **Backend:** Stores transactions in original currency
2. **Frontend:** Fetches transactions, optionally requests conversion
3. **Display Logic:**
   - If `showConverted` is true and currency differs from `displayCurrency`:
     - Show original amount in original currency
     - Show converted amount in display currency
     - Format: "$100.00 (from USD: $135.00 CAD)"
   - If same currency or `showConverted` is false:
     - Show only original amount

**Why Store Original Currency?**
- **Data Integrity:** Preserves original transaction data without modification.
- **Audit Trail:** Can always see what currency was actually used.
- **Accuracy:** Avoids rounding errors from multiple conversions.
- **Compliance:** Financial records should preserve original values.

**Why Client-Side Conversion?**
- **Real-Time Updates:** User can change display currency without server round-trip.
- **Performance:** Conversion is fast, no need to fetch from server.
- **Offline Capability:** Works even if backend is temporarily unavailable.
- **Flexibility:** User can toggle conversion on/off without affecting others.

**Why Show Both Original and Converted?**
- **Transparency:** Users understand the conversion is happening.
- **Trust:** Shows original value so users can verify conversion is correct.
- **Clarity:** Prevents confusion about which currency is being displayed.
- **Compliance:** Financial regulations often require showing original currency.

### Dark Mode Implementation

1. **Toggle:** `DarkModeToggle` component
2. **Persistence:** localStorage key `darkMode`
3. **Detection:** Checks system preference if no stored value
4. **Application:** Adds/removes `dark` class on `document.documentElement`
5. **Styling:** Tailwind `dark:` variants throughout
6. **Charts:** Uses `isDarkMode` state for tooltip styling (avoids SSR issues)

### State Management

**Dashboard (`index.tsx`):**
- Fetches transactions on mount
- Converts amounts when currency changes or `showConverted` toggles
- Tracks dark mode for chart tooltips (prevents SSR errors)

**Why useState Instead of Global State?**
- **Simplicity:** No need for Redux/Zustand for MVP scope.
- **Performance:** React's built-in state management is sufficient.
- **Maintainability:** Easier to understand and debug than global state.
- **Migration Path:** Can add state management library later if needed.

**Why Multiple useEffect Hooks?**
- **Separation of Concerns:** Each effect handles one responsibility.
- **Performance:** Effects only run when their dependencies change.
- **Debugging:** Easier to identify which effect is causing issues.

**Transactions (`transactions.tsx`):**
- Similar currency conversion logic
- Form state management
- Loading states

**Why Separate State for Form?**
- **Isolation:** Form state doesn't affect display until submitted.
- **UX:** Can reset form without affecting displayed transactions.
- **Validation:** Can validate form data before submission.

### Error Handling

- API calls wrapped in try-catch
- Console error logging
- Graceful fallbacks (e.g., currency conversion fails → show original amount)

**Why Try-Catch on API Calls?**
- **Resilience:** App continues working even if API fails.
- **User Experience:** Show meaningful errors instead of crashing.
- **Debugging:** Console logs help identify issues during development.

**Why Graceful Fallbacks?**
- **User Experience:** App degrades gracefully rather than breaking completely.
- **Reliability:** Core functionality (viewing transactions) works even if advanced features fail.
- **Progressive Enhancement:** Basic features work, enhanced features add value when available.

---

## Development Workflow

### Running Locally

1. **Start infrastructure:**
```bash
docker compose up -d
```

2. **Start backend (terminal 1):**
```bash
cd backend
source venv/bin/activate
PYTHONPATH=/path/to/canopy/backend python3 -m uvicorn app.server:app --reload --host 0.0.0.0 --port 8000
```

3. **Start frontend (terminal 2):**
```bash
cd frontend
npm run dev
```

### Testing

**Backend:**
```bash
cd backend
pytest
```

**Frontend:**
```bash
cd frontend
npm run lint
```

### Building for Production

**Backend:**
```bash
# No build step needed, but ensure dependencies are installed
pip install -r requirements.txt
```

**Frontend:**
```bash
cd frontend
npm run build
npm start
```

---

## Complete Feature Roadmap

Canopy is designed to be a comprehensive personal finance management application. The following is the complete list of functionalities that Canopy supports or will support:

### Core Features (MVP - Partially Implemented)
- ✅ **Dashboard**: View an overall summary of finances, insights, and activity reports
- ✅ **Transactions**: See, edit, categorize transactions; manual entries (export, rules, recurring - planned)
- 🔄 **Accounts**: Track and manage financial accounts (placeholder page created)
- 🔄 **Cash Flow**: Analyze income and expenses by category, merchant, and timeframe (basic charts implemented)
- 🔄 **Reports**: Generate detailed reports on spending, cash flow, and income analytics (basic implementation)

### Planned Features

#### Budgeting & Planning
- **Budget/Plan**: Set and monitor budgets, allocate funds, track actuals, and forecast expenses
- **Recurring Payments**: Manage subscriptions and regular payments
- **Goals/Objectives**: Create, track, and manage savings goals (e.g., retirement, travel)

#### Investment Management
- **Investments**: Monitor investment holdings, allocation, performance, and portfolio details (placeholder page created)

#### Financial Intelligence
- **Advice**: Receive financial recommendations, guidance, and tips
- **Assistant**: Get automated help or perform tasks within the app

#### User Management
- **Profile**: Edit personal data, household info, display, and notifications (settings page created)
- **Security**: Manage sign-in security and password controls
- **Members**: Add/manage household or family member access

#### Configuration & Preferences
- ✅ **Preferences**: Set language, currency, and display options (currency selector implemented)
- **Institutions**: Link/manage bank/financial connections
- **Categories**: Organize transactions and budgets by categories (basic support implemented)
- **Merchants**: Manage merchant data and group transactions
- **Rules**: Set up automation for categorization and alerts
- **Tags**: Tag and organize financial data

#### Data Management
- **Data**: Import/export options and integrations (CSV/OFX import planned)
- **Billing**: Monitor subscription/payment details
- **Referrals**: Manage and track referral rewards

### Technical Enhancements Needed
- Database persistence (currently in-memory)
- User authentication and authorization
- CSV/OFX import functionality
- Real-time exchange rate fetching
- Backup to S3-compatible storage
- Advanced reporting engine
- Notification system
- Search and filtering capabilities
- Bulk operations support

### Example Usage Scenarios

**Example 1:** "Show my investment performance and generate a cash flow report, then categorize recent transactions and update my budget forecast for November. Also, review security settings and add a new household member with access."

**Example 2:** "Import transactions from my bank CSV, apply categorization rules, create a budget for groceries and dining, set up a recurring payment reminder for my mortgage, and track progress toward my vacation savings goal."

**Example 3:** "Generate a spending report by category for the last quarter, identify top merchants, set up alerts for large transactions, and show me recommendations for reducing expenses."

### Implementation Priority

**Phase 1 (Current MVP):**
- ✅ Dashboard with basic stats and charts
- ✅ Transaction CRUD operations
- ✅ Multi-currency support
- ✅ Dark mode
- 🔄 Basic account management

**Phase 2 (Near-term):**
- Database persistence
- User authentication
- Category management
- Basic budgeting
- CSV import

**Phase 3 (Mid-term):**
- Investment tracking
- Advanced reporting
- Recurring transactions
- Goals tracking
- Rules engine

**Phase 4 (Long-term):**
- Financial advice engine
- Automated assistant
- Advanced analytics
- Bank integrations
- Mobile app

---

## Important Notes

1. **Current Storage:** Transactions are stored in-memory and will be lost on server restart. Database integration is planned.

2. **Exchange Rates:** Currently using mock exchange rates. Real API integration (e.g., exchangerate-api.io) should be added.

3. **CORS:** Currently allows all origins on localhost:3000. Should be restricted in production.

4. **Error Handling:** Basic error handling implemented. Should be enhanced with proper error responses and logging.

5. **Testing:** Unit tests not yet implemented. Should add pytest tests for backend and Jest/React Testing Library for frontend.

6. **Type Safety:** Frontend uses TypeScript, backend uses Pydantic for validation. Both should be strictly enforced.

7. **Performance:** Currency conversion happens client-side per transaction. Consider batching or server-side conversion for large datasets.

8. **Pydantic Version Compatibility:** The code uses `model_dump()` for Pydantic v2 compatibility with a fallback to `dict()` for Pydantic v1. Ensure you're using Pydantic v2 (`pydantic>=2.6.0`) for best compatibility.

---

## Troubleshooting

### Backend won't start
- Check Python version (3.10+)
- Verify virtual environment is activated
- Check PYTHONPATH is set correctly
- Ensure port 8000 is not in use

### Frontend won't start
- Check Node.js version (18+)
- Delete `node_modules` and `package-lock.json`, then `npm install`
- Check port 3000 is not in use

### Currency conversion not working
- Verify backend is running on port 8000
- Check browser console for CORS errors
- Verify API endpoint responds: `curl http://localhost:8000/v1/currency/supported`

### Dark mode not persisting
- Check browser localStorage is enabled
- Verify `DarkModeToggle` component is mounted
- Check browser console for errors

---

## Contact & Contribution

This master prompt should provide everything needed to recreate Canopy. For questions or contributions, refer to the main README.md.

---

**Last Updated:** 2024-01-15
**Version:** 0.1.0

