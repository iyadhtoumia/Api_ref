# API Documentation

## Base URL
```
http://localhost:5000
```

## Authentication
All protected endpoints require a JWT token in the Authorization header:
```
Authorization: Bearer <token>
```

---

## Endpoints

### 1. Sign Up (Create Account)

**Endpoint:** `POST /api/auth/signup`

**Description:** Create a new user account. New users receive 100 coins automatically.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response (201 Created):**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "coins": 100,
    "total_lookups": 0
  }
}
```

**Errors:**
- `400` - Email and password required
- `400` - Password must be at least 6 characters
- `400` - Email already registered

---

### 2. Sign In

**Endpoint:** `POST /api/auth/signin`

**Description:** Sign in to existing account

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response (200 OK):**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "coins": 90,
    "total_lookups": 1
  }
}
```

**Errors:**
- `400` - Email and password required
- `401` - Invalid email or password

---

### 3. Get Current User

**Endpoint:** `GET /api/auth/me`

**Description:** Get current user information (requires authentication)

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "coins": 90,
    "total_lookups": 1
  }
}
```

**Errors:**
- `401` - Token is missing
- `401` - Invalid token
- `401` - Token has expired

---

### 4. Lookup Configuration

**Endpoint:** `POST /api/lookup-config`

**Description:** Lookup device configuration by serial number (costs 10 coins, cached results are free)

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "serial": "C02P73J9G8WP"
}
```

**Response (200 OK):**
```json
{
  "serial": "C02P73J9G8WP",
  "config": "MacBook Pro 14-inch 2021, Carte logique (processeur Apple M1 Pro à 10 cœurs, 16 Go)",
  "cached": false,
  "coins_spent": 10
}
```

**Cached Response (200 OK):**
```json
{
  "serial": "C02P73J9G8WP",
  "config": "MacBook Pro 14-inch 2021, Carte logique (processeur Apple M1 Pro à 10 cœurs, 16 Go)",
  "cached": true,
  "coins_spent": 0
}
```

**Errors:**
- `400` - Serial number required
- `400` - Insufficient coins. You need 10 coins.
- `401` - Authentication errors
- `404` - Configuration not found
- `500` - Scraping error

---

### 5. Get Lookup History

**Endpoint:** `GET /api/history`

**Description:** Get user's lookup history (last 50 lookups)

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "history": [
    {
      "serial": "C02P73J9G8WP",
      "config": "MacBook Pro 14-inch 2021...",
      "coins_spent": 10,
      "created_at": "2024-01-15 10:30:00"
    }
  ]
}
```

---

### 6. Health Check

**Endpoint:** `GET /health`

**Description:** Check if API is running

**Response (200 OK):**
```json
{
  "status": "healthy"
}
```

---

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    coins INTEGER DEFAULT 100,
    total_lookups INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### Lookups Table
```sql
CREATE TABLE lookups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    serial TEXT NOT NULL,
    config TEXT NOT NULL,
    coins_spent INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
)
```

---

## Coin System

- **New User:** 100 coins
- **Cost per Lookup:** 10 coins
- **Cached Results:** FREE (0 coins)
- **Cache Duration:** 1 hour

---

## Authentication Flow

1. User signs up → Receives JWT token + 100 coins
2. Token stored in localStorage
3. Token sent with every request in Authorization header
4. Token expires after 30 days
5. User must sign in again to get new token

---

## Error Response Format

All errors return JSON with an error message:
```json
{
  "error": "Error message here"
}
```

Common HTTP status codes:
- `200` - Success
- `201` - Created (signup)
- `400` - Bad request (validation errors)
- `401` - Unauthorized (auth errors)
- `404` - Not found
- `500` - Server error
