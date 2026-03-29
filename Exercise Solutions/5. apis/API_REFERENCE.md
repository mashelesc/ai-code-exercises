# Task Manager API Reference

## Overview

The Task Manager API provides endpoints for user authentication, task management, and collaboration features. This document describes all available endpoints, their parameters, responses, and error handling.

**Base URL:** `http://localhost:5000`

**Content-Type:** `application/json`

---

## Authentication Endpoints

### Register User

**Endpoint:** `POST /api/users/register`

**Description:**
Register a new user account in the system. This endpoint handles user registration by accepting user credentials, validating input data, checking for existing accounts, and creating a new user record in the database. A confirmation token is generated and a confirmation email is sent to activate the account (errors in email sending do not block registration).

#### Request

**Method:** `POST`

**Headers:**
```
Content-Type: application/json
```

**Body:**
```json
{
  "username": "string",    // Unique username (required)
  "email": "string",       // Valid email address (required), will be lowercased
  "password": "string"     // Password, minimum 8 characters (required)
}
```

#### Response

**Success - 201 Created:**
```json
{
  "message": "User registered successfully",
  "user": {
    "id": "integer",              // New user ID
    "username": "string",         // Username
    "email": "string",            // Lowercased email
    "created_at": "string",       // ISO format timestamp
    "role": "string"              // Default role "user"
  }
}
```

**Error Responses:**

**400 Bad Request - Missing Field:**
```json
{
  "error": "Missing required field",
  "message": "<field> is required"
}
```
Triggered when: `username`, `email`, or `password` is not provided

**400 Bad Request - Invalid Email:**
```json
{
  "error": "Invalid email",
  "message": "Please provide a valid email address"
}
```
Triggered when: Email does not match format validation (regex: `^[^@]+@[^@]+\.[^@]+$`)

**400 Bad Request - Weak Password:**
```json
{
  "error": "Weak password",
  "message": "Password must be at least 8 characters long"
}
```
Triggered when: Password is less than 8 characters

**409 Conflict - Username Taken:**
```json
{
  "error": "Username taken",
  "message": "Username is already in use"
}
```
Triggered when: Username already exists in database

**409 Conflict - Email Exists:**
```json
{
  "error": "Email exists",
  "message": "An account with this email already exists"
}
```
Triggered when: Email already exists in database

**500 Internal Server Error:**
```json
{
  "error": "Server error",
  "message": "Failed to register user"
}
```
Triggered when: Database connection issues or unexpected server errors occur

#### Validation Rules

| Field | Rule | Details |
|-------|------|---------|
| `username` | Unique | Must not already exist in database; no format restrictions |
| `email` | Format + Unique | Must match regex `^[^@]+@[^@]+\.[^@]+$`; stored as lowercase |
| `password` | Minimum 8 chars | Hashed using pbkdf2 before storage |

#### Side Effects

- Creates new User record in database
- Hashes password using industry-standard hashing algorithm (pbkdf2)
- Generates confirmation token for email verification
- Attempts to send confirmation email (errors logged but non-blocking)
- Logs registration errors to application logger

#### Security Considerations

| Aspect | Description |
|--------|-------------|
| Password in Response | Not included in response for security |
| Password Storage | Hashed using pbkdf2, never stored as plaintext |
| Email Validation | Basic format check only; users must confirm email address |
| Data Integrity | Database transaction rolled back on any error |
| Log Information | Sensitive data (passwords) not logged |

#### Example Request

**cURL:**
```bash
curl -X POST http://localhost:5000/api/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "SecurePass123"
  }'
```

**JavaScript (Fetch):**
```javascript
fetch('http://localhost:5000/api/users/register', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    username: 'john_doe',
    email: 'john@example.com',
    password: 'SecurePass123'
  })
})
.then(response => response.json())
.then(data => console.log(data));
```

**Python (Requests):**
```python
import requests

response = requests.post(
    'http://localhost:5000/api/users/register',
    json={
        'username': 'john_doe',
        'email': 'john@example.com',
        'password': 'SecurePass123'
    }
)
print(response.json())
```

#### Important Notes

- Confirmation email sending failures are logged but do not prevent registration
- Multiple registration attempts with the same username/email will fail with appropriate conflict errors
- User role defaults to `"user"` on registration
- `created_at` timestamp is set to UTC time at registration
- Email address is automatically converted to lowercase for consistency

---

## Status Codes Reference

| Code | Name | Description |
|------|------|-------------|
| 201 | Created | Resource successfully created |
| 400 | Bad Request | Invalid input data or validation failed |
| 409 | Conflict | Resource already exists (username/email duplicate) |
| 500 | Internal Server Error | Server-side error occurred |

---

## Rate Limiting

Currently, no rate limiting is implemented. Future versions may include rate limiting to prevent abuse.

---

## Authentication

Password-based authentication with bearer tokens (implementation details TBD).

---

## Data Types

- **string:** Text data
- **integer:** Whole number
- **boolean:** True/False value
- **datetime:** ISO 8601 formatted timestamp (e.g., `2026-03-29T10:30:00`)

---

## Error Handling Best Practices

1. Always check the HTTP status code first
2. Parse the `error` field for error type
3. Read the `message` field for user-friendly error description
4. Implement retry logic for 5xx errors (with exponential backoff)
5. Log errors for debugging and monitoring

---

## Changelog

### Version 1.0.0 (Initial Release - March 29, 2026)

- ✅ User registration endpoint
- ✅ Email validation and format checking
- ✅ Password strength validation
- ✅ Duplicate account prevention
- ✅ Confirmation email sending

---

## Support

For issues or questions about the API, please refer to the project documentation or contact the development team.
