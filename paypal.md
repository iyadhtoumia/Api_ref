PayPal Integration Plan
Overview
The app uses Stripe for checkout. PayPal will be added as a second payment option. Users will choose between Stripe and PayPal in the "Add funds" modal.

Backend
Add paypalrestsdk (or paypalhttp + paypal-checkout-serversdk) to requirements.txt

Add PayPal credentials to config.py and .env.dev:

PAYPAL_CLIENT_ID
PAYPAL_CLIENT_SECRET
PAYPAL_MODE (sandbox or live)
Add a paypal_payments table to the DB (or extend payments with a provider column):

payments: add column provider TEXT DEFAULT 'stripe'
Add 3 new routes to backend_app.py:

POST /api/payments/paypal/create-order — creates a PayPal order, returns approve_url
POST /api/payments/paypal/capture-order — captures payment after user approves, credits balance
(optional) POST /api/payments/paypal/webhook — for IPN/webhook-based confirmation
Frontend
In Dashboard.jsx — update TopUpModal:

Add a method selector: "Stripe" | "PayPal" (two toggle buttons)
Stripe path stays the same (redirects to Stripe Checkout)
PayPal path: calls /api/payments/paypal/create-order, then redirects user to PayPal's approve_url
Handle PayPal return URLs (same pattern as Stripe):

success_url: /dashboard?payment=success&provider=paypal&token={token}
cancel_url: /dashboard?payment=cancel
On return, call /api/payments/paypal/capture-order with the PayPal token to finalize and credit balance
Environment / Config
Add to render.yaml (or your deployment config):
PAYPAL_CLIENT_ID
PAYPAL_CLIENT_SECRET
PAYPAL_MODE=live
Order of Implementation
DB migration (add provider column)
Backend routes (create-order → capture-order)
Frontend modal update (payment method toggle)
Handle redirect back from PayPal
Test in sandbox, then flip to live