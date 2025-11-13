# Canopy Architecture & Design Decisions

This document explains the "why" behind key architectural and design decisions in Canopy.

## Table of Contents
- [Architecture Overview](#architecture-overview)
- [Technology Choices](#technology-choices)
- [API Design](#api-design)
- [Frontend Architecture](#frontend-architecture)
- [Data Management](#data-management)
- [Security Considerations](#security-considerations)
- [Performance Optimizations](#performance-optimizations)

## Architecture Overview

### Monorepo Structure

**Decision:** Single repository for backend and frontend

**Why:**
- **Simplified Development:** One git repo, one clone, unified versioning
- **Atomic Commits:** Related frontend/backend changes can be committed together
- **Shared Types:** Can share TypeScript types between frontend and backend (future)
- **CI/CD Simplicity:** Single pipeline can build and test both
- **Team Coordination:** Easier to see full context of changes

**Trade-offs:**
- Larger repository size
- Requires discipline to keep concerns separated
- Alternative: Separate repos (more independence, more complex CI/CD)

### Backend-Frontend Separation

**Decision:** Separate FastAPI backend and Next.js frontend processes

**Why:**
- **Technology Fit:** Python excels at data processing, TypeScript/React for UI
- **Independent Scaling:** Can scale backend and frontend independently
- **Team Structure:** Backend and frontend developers can work independently
- **Deployment Flexibility:** Can deploy to different servers/regions
- **Testing:** Can test APIs independently of UI

**Trade-offs:**
- More complex deployment (two services to manage)
- CORS configuration needed
- Network latency between services
- Alternative: Server-side rendering with Python templates (simpler, less flexible)

## Technology Choices

### FastAPI Over Django/Flask

**Decision:** Use FastAPI for backend API

**Why:**
- **Performance:** Async/await support enables high concurrency
- **Type Safety:** Built-in Pydantic validation catches errors early
- **Auto Documentation:** OpenAPI/Swagger docs generated automatically
- **Modern Python:** Uses Python 3.10+ features (type hints, async)
- **Fast Development:** Less boilerplate than Django, more features than Flask

**Trade-offs:**
- Smaller ecosystem than Django
- Requires Python 3.7+ (not an issue for new projects)
- Alternative: Django (more batteries included, but heavier)

### Next.js Over Create React App

**Decision:** Use Next.js instead of plain React

**Why:**
- **SSR/SSG:** Better SEO and initial load performance
- **File-Based Routing:** Simpler than React Router configuration
- **Built-in Optimizations:** Image optimization, font optimization, code splitting
- **API Routes:** Can add backend endpoints if needed (not used currently)
- **Production Ready:** Optimized builds out of the box

**Trade-offs:**
- More complex than CRA for simple SPAs
- Requires understanding of SSR concepts
- Alternative: Vite + React (faster dev server, manual optimization)

### Tailwind CSS Over CSS Modules/Styled Components

**Decision:** Use Tailwind CSS utility-first approach

**Why:**
- **Rapid Development:** Write styles inline without context switching
- **Consistency:** Utility classes enforce design system automatically
- **Bundle Size:** Purged CSS removes unused styles (smaller bundles)
- **Dark Mode:** Built-in support via class strategy
- **Maintainability:** No CSS file sprawl, styles co-located with components

**Trade-offs:**
- Longer class names in JSX
- Learning curve for utility-first approach
- Alternative: CSS Modules (more traditional, requires separate files)

### In-Memory Storage Initially

**Decision:** Start with in-memory storage, plan database migration

**Why:**
- **MVP Speed:** Faster to prototype without database setup
- **Simplicity:** No migrations, connection pooling, or schema management
- **Testing:** Easy to reset state for tests
- **Focus:** Allows focusing on API design and UI first

**Trade-offs:**
- Data lost on restart (acceptable for MVP)
- No persistence (will be added)
- Alternative: Start with database (more complex setup, but persistent)

## API Design

### RESTful Endpoints

**Decision:** Use REST conventions for API design

**Why:**
- **Standard:** Familiar to most developers
- **HTTP Semantics:** Leverages HTTP methods (GET, POST, DELETE) naturally
- **Tooling:** Works with standard HTTP clients and tools
- **Documentation:** Easy to document and understand

**Alternative Considered:** GraphQL (more flexible queries, but more complex)

### Versioned API (`/v1/`)

**Decision:** Version API endpoints from the start

**Why:**
- **Future-Proofing:** Allows breaking changes in v2 without breaking v1 clients
- **Best Practice:** Industry standard for API evolution
- **Client Compatibility:** Multiple client versions can coexist
- **Clear Migration Path:** Obvious when to deprecate old versions

### Query Parameter for Currency Conversion

**Decision:** Use query parameter (`?currency=CAD`) instead of separate endpoint

**Why:**
- **RESTful:** GET requests should be idempotent, query params are filters
- **Flexibility:** Same endpoint serves multiple use cases
- **Caching:** Query params allow HTTP caching per currency
- **Simplicity:** One endpoint instead of `/transactions` and `/transactions/converted`

**Alternative:** Separate endpoint `/transactions/converted?currency=CAD` (more explicit, but violates DRY)

## Frontend Architecture

### Component-Based Structure

**Decision:** Organize by feature/component, not by file type

**Why:**
- **Co-location:** Related files stay together (component, styles, tests)
- **Discoverability:** Easy to find all code for a feature
- **Maintainability:** Changes to a feature are localized
- **Scalability:** Easy to add new features without restructuring

**Structure:**
```
components/
  Sidebar/
    Sidebar.tsx
    Sidebar.test.tsx
  StatCard/
    StatCard.tsx
```

**Alternative:** Group by type (all components, all tests separate) - harder to navigate

### Client-Side State Management

**Decision:** Use React useState/useEffect instead of Redux/Zustand initially

**Why:**
- **Simplicity:** Built-in state management sufficient for MVP scope
- **No Dependencies:** Reduces bundle size and complexity
- **Learning Curve:** Easier for developers new to the project
- **Migration Path:** Can add state management library when needed

**When to Add Redux/Zustand:**
- Shared state across many components
- Complex state logic
- Need for time-travel debugging
- Large team needing predictable state updates

### Dark Mode Implementation

**Decision:** Class-based dark mode with localStorage persistence

**Why:**
- **Performance:** Single DOM manipulation affects all elements
- **SSR Compatible:** Works with Next.js SSR without hydration issues
- **User Control:** Respects explicit user choice over system preference
- **Tailwind Integration:** Works seamlessly with Tailwind's dark mode

**Alternative:** CSS media queries (only respects system, no user control)

## Data Management

### Pydantic Models for Validation

**Decision:** Use Pydantic for all data validation

**Why:**
- **Type Safety:** Catches errors at API boundary, not deep in code
- **Auto Documentation:** FastAPI generates OpenAPI schema from models
- **Serialization:** Automatic JSON serialization/deserialization
- **Validation:** Built-in validators (email, URL, custom validators)

**Why Not:** Manual validation (error-prone, verbose, no type hints)

### Transaction Currency Storage

**Decision:** Store original currency, convert on-demand

**Why:**
- **Data Integrity:** Original transaction data preserved
- **Audit Trail:** Can always see original currency
- **Accuracy:** Avoids rounding errors from multiple conversions
- **Compliance:** Financial records should preserve original values

**Alternative:** Store in single currency (simpler, but loses original data)

### Mock Exchange Rates

**Decision:** Use hardcoded exchange rates initially

**Why:**
- **Development Speed:** No external API setup needed
- **Testing:** Predictable, reproducible rates
- **Offline:** Works without internet
- **Cost:** No API costs during development

**Future:** Integrate with exchange rate API (exchangerate-api.io, Fixer.io)

## Security Considerations

### CORS Configuration

**Decision:** Allow localhost:3000 in development

**Why:**
- **Development Necessity:** Frontend must call backend from different port
- **Security:** Restricted to specific origins (not `*`)
- **Future:** Will restrict to production domain in production

**Production Plan:** Replace with specific production domain

### No Authentication Initially

**Decision:** MVP without authentication

**Why:**
- **MVP Scope:** Focus on core functionality first
- **Local-First:** Self-hosted means network access control can provide security
- **Simplicity:** Faster to develop without auth complexity

**Future:** Add JWT-based authentication, rate limiting, API keys

### In-Memory Storage Security

**Decision:** Accept in-memory storage security implications for MVP

**Why:**
- **Temporary:** Will migrate to database with proper security
- **Local Only:** Self-hosted means data never leaves user's control
- **MVP Trade-off:** Acceptable risk for prototype

**Future:** Encrypted database, connection pooling, prepared statements

## Performance Optimizations

### Client-Side Currency Conversion

**Decision:** Convert currencies in frontend after fetching

**Why:**
- **Real-Time:** User can change display currency instantly
- **Reduced Server Load:** Server doesn't recalculate on every currency change
- **Offline Capable:** Works if backend temporarily unavailable
- **Flexibility:** Each user can view in their preferred currency

**Trade-off:** Multiple conversions if user changes currency frequently

**Future Optimization:** Cache converted amounts, batch conversions

### Conditional Router Loading

**Decision:** Use try/except to conditionally load routers

**Why:**
- **Flexibility:** App works even if some routers missing
- **Feature Flags:** Can enable/disable features easily
- **Development:** Can develop features in isolation

**Alternative:** Always require all routers (simpler, but less flexible)

### Recharts for Charts

**Decision:** Use Recharts instead of D3 directly

**Why:**
- **React Integration:** Declarative, React-friendly API
- **Responsive:** Built-in responsive behavior
- **Composability:** Components can be combined easily
- **Maintenance:** Active maintenance, good documentation

**Alternative:** D3.js (more powerful, but imperative, harder to integrate with React)

## Future Considerations

### Database Migration Strategy

**Plan:** Migrate from in-memory to PostgreSQL

**Why:**
- **Persistence:** Data survives server restarts
- **Concurrency:** Handles multiple users properly
- **Scalability:** Can scale beyond single server
- **Features:** Enables complex queries, reporting, analytics

**Migration Path:**
1. Keep in-memory as fallback
2. Add database layer behind same API
3. Migrate data on startup
4. Remove in-memory storage

### Authentication Strategy

**Plan:** JWT-based authentication

**Why:**
- **Stateless:** No server-side session storage needed
- **Scalable:** Works across multiple servers
- **Standard:** Industry-standard approach
- **Flexible:** Can add refresh tokens, roles, permissions

### Real Exchange Rate Integration

**Plan:** Integrate with exchange rate API

**Why:**
- **Accuracy:** Real-time or daily updated rates
- **Multiple Sources:** Can fallback if one API fails
- **Historical:** Can track rate changes over time

**Considerations:**
- Rate limits and costs
- Fallback to cached rates if API unavailable
- Update frequency (daily vs real-time)

---

**Last Updated:** 2025-11-04  
**Version:** 0.2.2

