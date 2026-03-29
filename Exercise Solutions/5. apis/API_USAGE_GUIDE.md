# Task Manager API Usage Guide

A practical guide to using the Task Manager API for developers. This guide provides step-by-step instructions, code examples, and best practices for integrating the API into your applications.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Authentication Flow](#authentication-flow)
3. [Common Use Cases](#common-use-cases)
4. [Error Handling](#error-handling)
5. [Best Practices](#best-practices)
6. [Troubleshooting](#troubleshooting)
7. [FAQ](#faq)

---

## Getting Started

### Prerequisites

Before you can use the Task Manager API, ensure you have:

- Access to a running Task Manager API server (default: `http://localhost:5000`)
- An HTTP client library or tool (cURL, Postman, Insomnia, etc.)
- Basic understanding of HTTP and JSON

### Installation & Setup

#### For JavaScript/Node.js

```bash
npm install axios
```

```javascript
const axios = require('axios');

const api = axios.create({
  baseURL: 'http://localhost:5000',
  headers: {
    'Content-Type': 'application/json'
  }
});
```

#### For Python

```bash
pip install requests
```

```python
import requests

API_BASE_URL = 'http://localhost:5000'
headers = {'Content-Type': 'application/json'}
```

#### For cURL

cURL is built into most Unix/Linux systems. For Windows, download from [curl.se](https://curl.se).

---

## Authentication Flow

### User Registration

The first step for new users is registration.

#### Step 1: Create a New Account

**Request:**
```bash
curl -X POST http://localhost:5000/api/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice_smith",
    "email": "alice@example.com",
    "password": "MySecurePassword123"
  }'
```

**Response (Success):**
```json
{
  "message": "User registered successfully",
  "user": {
    "id": 42,
    "username": "alice_smith",
    "email": "alice@example.com",
    "created_at": "2026-03-29T14:30:00",
    "role": "user"
  }
}
```

#### Step 2: Verify Email (Asynchronous)

After registration, a confirmation email is sent to `alice@example.com`. The user must:

1. Check their inbox for the confirmation link
2. Click the confirmation link to activate their account
3. Once confirmed, they can log in

#### Step 3: Log In (Future Enhancement)

```bash
# This endpoint will be available in a future version
curl -X POST http://localhost:5000/api/users/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice_smith",
    "password": "MySecurePassword123"
  }'
```

---

## Common Use Cases

### Use Case 1: Register a New User

**Scenario:** A user visits your application and wants to create an account.

**Steps:**

1. Collect user input (username, email, password)
2. Validate input on client side
3. Send registration request
4. Handle response and confirm with user

**JavaScript Example:**

```javascript
async function registerUser(username, email, password) {
  try {
    const response = await api.post('/api/users/register', {
      username,
      email,
      password
    });

    console.log('Registration successful!');
    console.log('User ID:', response.data.user.id);
    console.log('Confirmation email sent to:', response.data.user.email);

    return response.data;
  } catch (error) {
    handleRegistrationError(error);
  }
}

function handleRegistrationError(error) {
  if (error.response) {
    const status = error.response.status;
    const errorData = error.response.data;

    if (status === 400) {
      console.error('Validation Error:', errorData.message);
      // Show user-friendly message
    } else if (status === 409) {
      console.error('Conflict:', errorData.message);
      // Username or email already exists
    } else if (status === 500) {
      console.error('Server Error:', errorData.message);
      // Try again later
    }
  }
}
```

**Python Example:**

```python
def register_user(username, email, password):
    """Register a new user with the API."""
    try:
        response = requests.post(
            f'{API_BASE_URL}/api/users/register',
            headers=headers,
            json={
                'username': username,
                'email': email,
                'password': password
            }
        )
        
        if response.status_code == 201:
            user_data = response.json()
            print(f"✓ Registration successful!")
            print(f"User ID: {user_data['user']['id']}")
            print(f"Confirmation email sent to: {user_data['user']['email']}")
            return user_data
        
        elif response.status_code in [400, 409]:
            error_data = response.json()
            print(f"✗ Error: {error_data['message']}")
            return None
    
    except requests.RequestException as e:
        print(f"✗ Network error: {str(e)}")
        return None
```

### Use Case 2: Bulk User Registration (Batch)

**Scenario:** Importing users from a CSV file or batch registration.

**CSV File Format:**
```
username,email,password
john_doe,john@example.com,SecurePass123
jane_smith,jane@example.com,AnotherPass456
bob_jones,bob@example.com,ThirdPass789
```

**Python Implementation:**

```python
import csv
import time

def bulk_register_users(csv_file):
    """Register multiple users from a CSV file."""
    successful = 0
    failed = 0
    results = []

    with open(csv_file, 'r') as file:
        reader = csv.DictReader(file)
        
        for row in reader:
            try:
                response = requests.post(
                    f'{API_BASE_URL}/api/users/register',
                    headers=headers,
                    json={
                        'username': row['username'],
                        'email': row['email'],
                        'password': row['password']
                    },
                    timeout=5
                )
                
                if response.status_code == 201:
                    successful += 1
                    results.append({
                        'username': row['username'],
                        'status': 'SUCCESS',
                        'user_id': response.json()['user']['id']
                    })
                else:
                    failed += 1
                    results.append({
                        'username': row['username'],
                        'status': 'FAILED',
                        'reason': response.json().get('message', 'Unknown error')
                    })
                
                # Rate limiting: wait 0.5 seconds between requests
                time.sleep(0.5)
            
            except Exception as e:
                failed += 1
                results.append({
                    'username': row['username'],
                    'status': 'ERROR',
                    'reason': str(e)
                })

    print(f"\n--- Bulk Registration Report ---")
    print(f"Total: {successful + failed}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {(successful / (successful + failed) * 100):.1f}%")
    
    return results
```

### Use Case 3: Form Validation Before Submission

**Scenario:** Client-side validation before sending a registration request to minimize errors.

**JavaScript Example:**

```javascript
class RegistrationValidator {
  static validateUsername(username) {
    if (!username) return 'Username is required';
    if (username.length < 3) return 'Username must be at least 3 characters';
    if (username.length > 50) return 'Username must be 50 characters or less';
    if (!/^[a-zA-Z0-9_-]+$/.test(username)) {
      return 'Username can only contain letters, numbers, hyphens, and underscores';
    }
    return null; // Valid
  }

  static validateEmail(email) {
    if (!email) return 'Email is required';
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      return 'Please enter a valid email address';
    }
    return null; // Valid
  }

  static validatePassword(password) {
    if (!password) return 'Password is required';
    if (password.length < 8) return 'Password must be at least 8 characters';
    if (!/[a-z]/.test(password)) return 'Password must contain lowercase letters';
    if (!/[A-Z]/.test(password)) return 'Password must contain uppercase letters';
    if (!/[0-9]/.test(password)) return 'Password must contain numbers';
    return null; // Valid
  }

  static validateAll(username, email, password) {
    const errors = {};
    
    let usernameError = this.validateUsername(username);
    if (usernameError) errors.username = usernameError;
    
    let emailError = this.validateEmail(email);
    if (emailError) errors.email = emailError;
    
    let passwordError = this.validatePassword(password);
    if (passwordError) errors.password = passwordError;

    return Object.keys(errors).length === 0 ? null : errors;
  }
}

// Usage
const validationErrors = RegistrationValidator.validateAll(
  'alice_smith',
  'alice@example.com',
  'MySecurePassword123'
);

if (validationErrors) {
  console.log('Validation failed:', validationErrors);
} else {
  console.log('All validations passed!');
  // Proceed with API call
}
```

---

## Error Handling

### Understanding Error Responses

Every error response includes:
- **HTTP Status Code**: Indicates the category of error
- **error**: Machine-readable error identifier
- **message**: Human-readable error description

### Error Categories

#### 400 Bad Request

These errors indicate the request data is invalid. **Action**: Fix the request and retry.

**Example:**
```json
{
  "error": "Weak password",
  "message": "Password must be at least 8 characters long"
}
```

#### 409 Conflict

These errors indicate a resource already exists. **Action**: Use different values or check with the user.

**Example:**
```json
{
  "error": "Email exists",
  "message": "An account with this email already exists"
}
```

#### 500 Internal Server Error

These errors indicate a server-side problem. **Action**: Retry after a delay (exponential backoff).

**Example:**
```json
{
  "error": "Server error",
  "message": "Failed to register user"
}
```

### Implementing Robust Error Handling

**JavaScript with Retry Logic:**

```javascript
async function apiRequestWithRetry(
  method,
  endpoint,
  data,
  maxRetries = 3
) {
  let lastError;

  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const response = await api({
        method,
        url: endpoint,
        data
      });
      return response.data;
    } catch (error) {
      lastError = error;

      // Don't retry for client errors (400, 409)
      if (error.response && error.response.status < 500) {
        throw error;
      }

      // Retry for server errors (500+) with exponential backoff
      if (attempt < maxRetries) {
        const delay = Math.pow(2, attempt) * 1000; // 2s, 4s, 8s
        console.log(`Retry attempt ${attempt} after ${delay}ms`);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }

  throw lastError;
}

// Usage
try {
  const result = await apiRequestWithRetry('POST', '/api/users/register', {
    username: 'alice',
    email: 'alice@example.com',
    password: 'SecurePassword123'
  });
  console.log('Success:', result);
} catch (error) {
  if (error.response) {
    console.error('API Error:', error.response.data.message);
  } else {
    console.error('Network Error:', error.message);
  }
}
```

---

## Best Practices

### 1. Password Security

✅ **DO:**
- Enforce strong password requirements (min 8 characters, mixed case, numbers)
- Use HTTPS to encrypt passwords in transit
- Hash passwords server-side before storage
- Never log or display passwords

❌ **DON'T:**
- Accept weak passwords
- Send passwords in URLs or logs
- Store passwords in browser localStorage
- Transmit over unencrypted connections

**Example:**
```javascript
// Hash password client-side (optional but recommended)
async function hashPasswordClientSide(password) {
  const encoder = new TextEncoder();
  const data = encoder.encode(password);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}
```

### 2. Email Validation

✅ **DO:**
- Validate email format client-side
- Require email confirmation for new accounts
- Handle email delivery failures gracefully

❌ **DON'T:**
- Trust unconfirmed emails
- Use punycode domains without testing
- Assume email format is 100% validated

**Example:**
```javascript
function isValidEmail(email) {
  // RFC 5322 simplified pattern
  const pattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return pattern.test(email);
}
```

### 3. Rate Limiting Awareness

✅ **DO:**
- Implement client-side delays for batch operations
- Respect server rate limits when they're implemented
- Cache responses when appropriate
- Handle 429 (Too Many Requests) responses

**Example:**
```javascript
class RateLimiter {
  constructor(requestsPerSecond = 10) {
    this.requestsPerSecond = requestsPerSecond;
    this.queue = [];
    this.processing = false;
  }

  async execute(fn) {
    return new Promise(resolve => {
      this.queue.push({ fn, resolve });
      this.process();
    });
  }

  async process() {
    if (this.processing || this.queue.length === 0) return;
    this.processing = true;

    while (this.queue.length > 0) {
      const { fn, resolve } = this.queue.shift();
      const result = await fn();
      resolve(result);

      // Wait between requests
      await new Promise(r => 
        setTimeout(r, 1000 / this.requestsPerSecond)
      );
    }

    this.processing = false;
  }
}
```

### 4. Logging and Monitoring

✅ **DO:**
- Log API responses (but not passwords)
- Track error rates and types
- Monitor API response times
- Alert on repeated failures

❌ **DON'T:**
- Log sensitive user data
- Log full request/response bodies
- Store logs without encryption
- Ignore error patterns

**Example:**
```python
import logging
from datetime import datetime

logging.basicConfig(
    filename='api_calls.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def log_api_call(method, endpoint, status_code, response_time):
    """Log API call details without sensitive data."""
    logging.info(
        f"{method} {endpoint} - Status: {status_code} - "
        f"Time: {response_time:.2f}s"
    )
```

---

## Troubleshooting

### Problem: "Connection Refused"

**Symptom:** Cannot connect to API server

**Solutions:**
1. Verify the API server is running
2. Check the correct base URL
3. Verify firewall rules allow the connection
4. Check if port 5000 is in use

**Debug:**
```bash
# Test if server is running
curl -I http://localhost:5000/api/users/register

# Check if port is listening
netstat -an | grep 5000

# Ping the server
ping localhost
```

### Problem: "401 Unauthorized"

**Symptom:** Request rejected with authentication error

**Solutions:**
1. Ensure you're logged in
2. Check if session token is valid
3. Verify API key (if required)

### Problem: "400 Bad Request - Weak Password"

**Symptom:** Password validation fails

**Solutions:**
1. Password must be at least 8 characters
2. Ensure it contains mixed case and numbers
3. Avoid common patterns (123456, password, qwerty)

**Test:**
```javascript
const testPasswords = [
  'abc123',        // ❌ Too short
  'password',      // ❌ No numbers
  'PASSWORD123',   // ❌ No lowercase
  'Pass123',       // ❌ Too short (7 chars)
  'MyPass1234',    // ✅ Valid
];
```

### Problem: "409 Conflict - Email exists"

**Symptom:** Email already registered

**Solutions:**
1. Use a different email address
2. If it's your email, use "Forgot Password" to recover account
3. Check for typos in the email

### Problem: "500 Internal Server Error"

**Symptom:** Server-side error

**Solutions:**
1. Wait a moment and retry
2. Check API server logs
3. Contact API support

**Debug:**
```bash
# Check server logs
tail -f /path/to/api/logs/app.log

# Restart the API server (if you have access)
sudo systemctl restart task-manager-api
```

---

## FAQ

### Q: How long does email confirmation take?

**A:** Email confirmation is sent immediately, but may take 1-5 minutes to arrive. Check spam folder. If not received within 10 minutes, contact support.

### Q: Can I change my username after registration?

**A:** This depends on API configuration. Currently, usernames are permanent. Contact support if username change is needed.

### Q: Is my password encrypted?

**A:** Yes. Passwords are:
1. Transmitted over HTTPS (encrypted in transit)
2. Hashed using pbkdf2 before storage (encrypted at rest)
3. Never stored in plaintext

### Q: What happens if I forget my password?

**A:** Feature coming soon. For now, contact support for account recovery.

### Q: Are there usage limits?

**A:** Currently, no explicit rate limits. However, excessive requests may be rate-limited in future versions. Best practice: implement delays between requests.

### Q: Can I delete my account?

**A:** Account deletion is not yet available. This feature will be added in a future release.

### Q: How is my data protected?

**A:** Data protection measures include:
- HTTPS encryption for transit
- Password hashing for storage
- Database access controls
- Regular backups
- (Future) Two-factor authentication

### Q: What's the API response time expectation?

**A:** Typical response times:
- Registration: 100-500ms
- Email sending: 1-5 seconds (asynchronous)

### Q: Can I use the API from a mobile app?

**A:** Yes, any HTTP client (native, React Native, Flutter, etc.) can use the API. Use HTTPS in production.

### Q: Is there an API SDK available?

**A:** SDKs for popular languages are planned for future releases. Currently, use HTTP clients (axios, requests, fetch, etc.).

---

## Support and Resources

- **API Reference**: See [API_REFERENCE.md](API_REFERENCE.md)
- **Project Documentation**: See [README.md](README.md)
- **Bug Reports**: Open an issue in the project repository
- **Feature Requests**: Submit via GitHub Discussions
- **Email Support**: support@taskmanager.local (future)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-29 | Initial release with user registration |
| (Future) | TBD | Login, password reset, user profile endpoints |

---

**Last Updated:** March 29, 2026  
**API Version:** 1.0.0
