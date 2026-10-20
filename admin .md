Admin Panel Plan
1. Auth & Access
Add is_admin INTEGER DEFAULT 0 column to users table
Admin account created at startup via env vars (ADMIN_EMAIL / ADMIN_PASSWORD) — idempotent, won't duplicate
New admin_required decorator on the backend (wraps token_required, checks is_admin = 1)
Frontend: AdminRoute component that reads is_admin from the JWT/user context, redirects to /signin otherwise
2. Backend — new routes (all under /api/admin/...)
Route	What it does
GET /api/admin/stats	Total users, revenue, lookups today/all-time, top 5 services
GET /api/admin/users	Paginated user list with search
PATCH /api/admin/users/:id	Adjust balance, toggle ban, manual verify
DELETE /api/admin/users/:id	Delete account
GET /api/admin/services	All services (active + inactive)
PATCH /api/admin/services/:id	Edit name, price, category, toggle active
POST /api/admin/services	Add a new service
DELETE /api/admin/services/:id	Remove a service
GET /api/admin/transactions	Unified payments + lookups ledger, filterable
POST /api/admin/transactions/refund/:payment_id	Refund — credits balance, marks payment as refunded
3. Frontend — new pages under /admin
/admin                → redirect to /admin/dashboard
/admin/dashboard      → stats cards + charts
/admin/users          → table, search, inline actions
/admin/services       → table, inline edit, add/delete
/admin/transactions   → unified ledger with filters
New files:

frontend/src/pages/admin/
  AdminLayout.jsx       ← sidebar + admin nav shell
  AdminDashboard.jsx    ← stats/charts
  AdminUsers.jsx        ← user management
  AdminServices.jsx     ← service/API management
  AdminTransactions.jsx ← payments + lookups ledger
App.jsx gets an AdminRoute guard. AuthContext exposes user.is_admin.

4. DB changes
users table: + is_admin INTEGER DEFAULT 0
payments table: + refunded_at TIMESTAMP (for refund tracking)
No new tables needed
Implementation order
DB migration + admin account bootstrap in backend_app.py
admin_required decorator + all admin routes
Frontend AdminRoute, AdminLayout, then pages one by one