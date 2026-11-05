#!/bin/bash
# Authentication Flow Test Script
# Quick manual test of JWT authentication

set -e  # Exit on error

API_URL="${API_URL:-http://localhost:8000}"
USERNAME="${USERNAME:-testuser}"
PASSWORD="${PASSWORD:-testpass}"

echo "========================================"
echo "MAAPS API Authentication Test"
echo "========================================"
echo "API URL: $API_URL"
echo "Username: $USERNAME"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test 1: Check API is running
echo -e "${BLUE}Test 1: Checking if API is running...${NC}"
if curl -s -f "$API_URL/" > /dev/null; then
    echo -e "${GREEN}✓ API is running${NC}"
else
    echo -e "${RED}✗ API is not responding${NC}"
    echo "Start the API with: uvicorn api.main:app --reload"
    exit 1
fi
echo ""

# Test 2: Login and get token
echo -e "${BLUE}Test 2: Login and get JWT token...${NC}"
LOGIN_RESPONSE=$(curl -s -X POST "$API_URL/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"username\": \"$USERNAME\", \"password\": \"$PASSWORD\"}")

TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['token'])" 2>/dev/null || echo "")

if [ -n "$TOKEN" ]; then
    echo -e "${GREEN}✓ Login successful${NC}"
    echo "Token (first 50 chars): ${TOKEN:0:50}..."
    echo "Full response: $LOGIN_RESPONSE"
else
    echo -e "${RED}✗ Login failed${NC}"
    echo "Response: $LOGIN_RESPONSE"
    exit 1
fi
echo ""

# Test 3: Verify token
echo -e "${BLUE}Test 3: Verify token...${NC}"
VERIFY_RESPONSE=$(curl -s -X GET "$API_URL/auth/verify" \
    -H "Authorization: Bearer $TOKEN")

if echo "$VERIFY_RESPONSE" | grep -q "\"valid\":true"; then
    echo -e "${GREEN}✓ Token is valid${NC}"
    echo "Response: $VERIFY_RESPONSE"
else
    echo -e "${RED}✗ Token verification failed${NC}"
    echo "Response: $VERIFY_RESPONSE"
    exit 1
fi
echo ""

# Test 4: Access protected endpoint WITH token
echo -e "${BLUE}Test 4: Access protected endpoint WITH token...${NC}"
RESTART_RESPONSE=$(curl -s -X POST "$API_URL/system/restart" \
    -H "Authorization: Bearer $TOKEN")

if echo "$RESTART_RESPONSE" | grep -q "\"status\":\"success\""; then
    echo -e "${GREEN}✓ Protected endpoint accessible with token${NC}"
    echo "Response: $RESTART_RESPONSE"
else
    echo -e "${RED}✗ Protected endpoint failed${NC}"
    echo "Response: $RESTART_RESPONSE"
    # Don't exit, continue with other tests
fi
echo ""

# Test 5: Access protected endpoint WITHOUT token
echo -e "${BLUE}Test 5: Access protected endpoint WITHOUT token (should fail)...${NC}"
NO_AUTH_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "$API_URL/system/restart")
HTTP_CODE=$(echo "$NO_AUTH_RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)

if [ "$HTTP_CODE" = "403" ] || [ "$HTTP_CODE" = "401" ]; then
    echo -e "${GREEN}✓ Protected endpoint correctly rejected request without token${NC}"
    echo "HTTP Status: $HTTP_CODE"
else
    echo -e "${RED}✗ Protected endpoint should reject requests without token${NC}"
    echo "HTTP Status: $HTTP_CODE"
fi
echo ""

# Test 6: Access optional auth endpoint WITH token
echo -e "${BLUE}Test 6: Access optional auth endpoint WITH token...${NC}"
GENERATE_WITH_AUTH=$(curl -s -X POST "$API_URL/audio/generate" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "content_type": "melody",
        "key": "C major",
        "tempo": 120,
        "time_signature": "4/4",
        "chord_progression": ["C", "Am", "F", "G"],
        "length_bars": 8
    }')

if echo "$GENERATE_WITH_AUTH" | grep -q "authenticated_user"; then
    echo -e "${GREEN}✓ Optional auth endpoint recognizes authenticated user${NC}"
    echo "Response includes authenticated_user field"
else
    echo -e "${RED}✗ Optional auth endpoint should include user context${NC}"
    echo "Response: $GENERATE_WITH_AUTH"
fi
echo ""

# Test 7: Access optional auth endpoint WITHOUT token
echo -e "${BLUE}Test 7: Access optional auth endpoint WITHOUT token...${NC}"
GENERATE_NO_AUTH=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "$API_URL/audio/generate" \
    -H "Content-Type: application/json" \
    -d '{
        "content_type": "melody",
        "key": "C major",
        "tempo": 120,
        "time_signature": "4/4",
        "chord_progression": ["C", "Am", "F", "G"],
        "length_bars": 8
    }')
HTTP_CODE=$(echo "$GENERATE_NO_AUTH" | grep "HTTP_CODE" | cut -d: -f2)

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ Optional auth endpoint works without token${NC}"
    if ! echo "$GENERATE_NO_AUTH" | grep -q "authenticated_user"; then
        echo -e "${GREEN}✓ Response correctly omits authenticated_user field${NC}"
    fi
else
    echo -e "${RED}✗ Optional auth endpoint should work without token${NC}"
    echo "HTTP Status: $HTTP_CODE"
fi
echo ""

# Test 8: Public endpoints
echo -e "${BLUE}Test 8: Public endpoints (no auth required)...${NC}"
PUBLIC_ENDPOINTS=(
    "GET:/"
    "GET:/health"
    "GET:/metrics"
    "GET:/agents"
    "GET:/system/version"
    "GET:/audio/formats"
)

for endpoint in "${PUBLIC_ENDPOINTS[@]}"; do
    METHOD=$(echo "$endpoint" | cut -d: -f1)
    PATH=$(echo "$endpoint" | cut -d: -f2)

    RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X "$METHOD" "$API_URL$PATH")
    HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)

    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "${GREEN}✓ $METHOD $PATH${NC}"
    else
        echo -e "${RED}✗ $METHOD $PATH (HTTP $HTTP_CODE)${NC}"
    fi
done
echo ""

# Summary
echo "========================================"
echo -e "${GREEN}Authentication test complete!${NC}"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Review AUTHENTICATION_GUIDE.md for detailed documentation"
echo "2. Run pytest tests: pytest tests/test_authentication.py"
echo "3. Update production .env.production with secure JWT_SECRET"
echo ""
