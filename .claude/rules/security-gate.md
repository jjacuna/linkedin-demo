# Security Gate — Runs After QA Passes

## Input Validation & Sanitization
- All user inputs sanitized (prevent XSS)
- Parameterized queries for all database operations (prevent SQL injection)
- File uploads restricted by type, size, scanned for malicious content
- URL parameters and query strings validated

## Authentication & Authorization
- Auth flows secure (login, logout, session management)
- API keys, tokens, secrets NOT in client-side code
- Role-based access control (RBAC) where applicable
- JWT/session tokens handled securely (httpOnly, secure, sameSite)
- Passwords hashed with bcrypt (min 12 rounds)
- Rate limiting on login endpoints

## Data Protection
- HTTPS/TLS enforced — no exceptions
- No sensitive data in localStorage or console logs
- Environment variables for all credentials
- CORS policies properly configured
- Content Security Policy (CSP) headers set

## HTTP Security Headers
- `Strict-Transport-Security` (HSTS)
- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy` configured

## Dependencies
- No known CVEs in third-party packages
- Packages up to date (run `npm audit` equivalent)
- Lockfile committed (package-lock.json or yarn.lock)
- Minimal dependency footprint — don't add what you don't need

## Error Handling
- Error messages don't expose stack traces or system info
- Graceful degradation on API failures
- Logging captures errors server-side without leaking to client

## Report Format
```
🔒 SECURITY REPORT
Input Validation:  [PASS/FAIL] — [details]
Auth & Access:     [PASS/FAIL] — [details]
Data Protection:   [PASS/FAIL] — [details]
Headers & Config:  [PASS/FAIL] — [details]
Dependencies:      [PASS/FAIL] — [details]
Error Handling:    [PASS/FAIL] — [details]
Risk Level: [Low / Medium / High / Critical]
Status: [SECURE / VULNERABILITIES FOUND]
```
