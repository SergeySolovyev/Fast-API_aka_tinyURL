# API Testing Examples

## Base URL
```
LOCAL: http://localhost:8000
RENDER: https://your-app.onrender.com
```

## 1. Register User
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123"
  }'
```

## 2. Login (Get JWT Token)
```bash
curl -X POST http://localhost:8000/auth/jwt/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=testpassword123"
```

Save token from response:
```bash
export TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

## 3. Create Short Link (Anonymous)
```bash
curl -X POST http://localhost:8000/links/shorten \
  -H "Content-Type: application/json" \
  -d '{
    "original_url": "https://github.com/SergeySolovyev"
  }'
```

## 4. Create Short Link with Custom Alias (Authenticated)
```bash
curl -X POST http://localhost:8000/links/shorten \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "original_url": "https://www.hse.ru",
    "custom_alias": "hse-main"
  }'
```

## 5. Create Link with Expiration
```bash
curl -X POST http://localhost:8000/links/shorten \
  -H "Content-Type: application/json" \
  -d '{
    "original_url": "https://example.com/temporary",
    "expires_at": "2026-12-31T23:59:59"
  }'
```

## 6. Redirect via Short Code
```bash
curl -L http://localhost:8000/abc123
```

## 7. Get Link Statistics
```bash
curl http://localhost:8000/links/abc123/stats
```

## 8. Search Links by URL
```bash
curl "http://localhost:8000/links/search/by-url?original_url=https://github.com/SergeySolovyev"
```

## 9. Get My Links (Authenticated)
```bash
curl http://localhost:8000/links/user/my-links \
  -H "Authorization: Bearer $TOKEN"
```

## 10. Update Link (Authenticated)
```bash
curl -X PUT http://localhost:8000/links/abc123 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "original_url": "https://new-url.com",
    "category": "personal"
  }'
```

## 11. Delete Link (Authenticated)
```bash
curl -X DELETE http://localhost:8000/links/abc123 \
  -H "Authorization: Bearer $TOKEN"
```

## 12. Health Check
```bash
curl http://localhost:8000/health
```

## Complete Testing Script
```bash
#!/bin/bash

BASE_URL="http://localhost:8000"

# Register
echo "=== Registering user ==="
curl -X POST $BASE_URL/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@test.com", "password": "test1234"}'

# Login and extract token
echo -e "\n\n=== Logging in ==="
TOKEN=$(curl -s -X POST $BASE_URL/auth/jwt/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@test.com&password=test1234" | jq -r .access_token)

echo "Token: $TOKEN"

# Create anonymous link
echo -e "\n\n=== Creating anonymous link ==="
curl -X POST $BASE_URL/links/shorten \
  -H "Content-Type: application/json" \
  -d '{"original_url": "https://github.com"}'

# Create authenticated link with alias
echo -e "\n\n=== Creating link with custom alias ==="
RESPONSE=$(curl -s -X POST $BASE_URL/links/shorten \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"original_url": "https://www.hse.ru", "custom_alias": "hse"}')

echo $RESPONSE

SHORT_CODE=$(echo $RESPONSE | jq -r .short_code)

# Get stats
echo -e "\n\n=== Getting link stats ==="
curl $BASE_URL/links/$SHORT_CODE/stats

# Test redirect (won't follow)
echo -e "\n\n=== Testing redirect ==="
curl -I $BASE_URL/$SHORT_CODE

# Get my links
echo -e "\n\n=== My links ==="
curl $BASE_URL/links/user/my-links \
  -H "Authorization: Bearer $TOKEN"

echo -e "\n\n=== Done ==="
```

Save as `test_api.sh` and run: `chmod +x test_api.sh && ./test_api.sh`
