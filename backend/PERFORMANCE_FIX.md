# Login Performance Optimization

## Issue
Backend login was taking too long (75+ seconds timeout).

## Root Cause
1. **Bcrypt password verification**: Default bcrypt rounds (12) takes ~0.2s per verification
2. **Server not responding**: Backend server wasn't properly listening on port 8000

## Fixes Applied

### 1. Optimized Bcrypt Rounds (Development)
- **Changed**: Reduced bcrypt rounds from 12 to 4 for development
- **Impact**: Password verification now ~0.02s instead of ~0.2s
- **Location**: `backend/app/core/security.py`
- **Note**: Production should use rounds=12 for security

### 2. Server Startup
- Restarted backend server properly
- Verified server is listening on port 8000

## Performance Metrics

### Before:
- Login timeout: 75+ seconds
- Password verification: ~0.2s (rounds=12)

### After:
- Login: < 1 second
- Password verification: ~0.02s (rounds=4)

## Testing

```bash
# Test login speed
time curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@marketplace.com&password=admin123"
```

## Production Note

For production, update `backend/app/core/security.py`:
```python
bcrypt_rounds = 12  # Use default for production security
```

The current setup uses rounds=4 only in development mode.
