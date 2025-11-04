#!/bin/bash
# LedgerLight Application Test Script
# This script tests all functionality of the LedgerLight application

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
BACKEND_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:3000"
BACKEND_PORT=8000
FRONTEND_PORT=3000

echo -e "${GREEN}=== LedgerLight Application Test Suite ===${NC}\n"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a port is in use
port_in_use() {
    lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1
}

# Function to wait for a service to be ready
wait_for_service() {
    local url=$1
    local max_attempts=30
    local attempt=1
    
    echo -e "${YELLOW}Waiting for service at $url...${NC}"
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Service is ready${NC}"
            return 0
        fi
        echo -n "."
        sleep 1
        attempt=$((attempt + 1))
    done
    echo -e "\n${RED}✗ Service failed to start${NC}"
    return 1
}

# Function to test API endpoint
test_endpoint() {
    local method=$1
    local endpoint=$2
    local data=$3
    local expected_status=${4:-200}
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$BACKEND_URL$endpoint")
    elif [ "$method" = "POST" ]; then
        response=$(curl -s -w "\n%{http_code}" -X POST \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$BACKEND_URL$endpoint")
    elif [ "$method" = "DELETE" ]; then
        response=$(curl -s -w "\n%{http_code}" -X DELETE "$BACKEND_URL$endpoint")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" = "$expected_status" ]; then
        echo -e "${GREEN}✓${NC} $method $endpoint - Status: $http_code"
        return 0
    else
        echo -e "${RED}✗${NC} $method $endpoint - Expected: $expected_status, Got: $http_code"
        echo "  Response: $body"
        return 1
    fi
}

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"
missing_deps=0

if ! command_exists python3; then
    echo -e "${RED}✗ Python 3 is not installed${NC}"
    missing_deps=1
else
    echo -e "${GREEN}✓${NC} Python 3 found: $(python3 --version)"
fi

if ! command_exists node; then
    echo -e "${RED}✗ Node.js is not installed${NC}"
    missing_deps=1
else
    echo -e "${GREEN}✓${NC} Node.js found: $(node --version)"
fi

if ! command_exists curl; then
    echo -e "${RED}✗ curl is not installed${NC}"
    missing_deps=1
else
    echo -e "${GREEN}✓${NC} curl found"
fi

if [ $missing_deps -eq 1 ]; then
    echo -e "\n${RED}Please install missing dependencies before running tests${NC}"
    exit 1
fi

echo ""

# Check if services are running
echo -e "${YELLOW}Checking if services are running...${NC}"

if ! port_in_use $BACKEND_PORT; then
    echo -e "${RED}✗ Backend is not running on port $BACKEND_PORT${NC}"
    echo -e "${YELLOW}Please start the backend with:${NC}"
    echo "  cd backend && source venv/bin/activate"
    echo "  PYTHONPATH=.. python3 -m uvicorn app.server:app --reload --host 0.0.0.0 --port 8000"
    exit 1
else
    echo -e "${GREEN}✓${NC} Backend is running on port $BACKEND_PORT"
fi

if ! port_in_use $FRONTEND_PORT; then
    echo -e "${RED}✗ Frontend is not running on port $FRONTEND_PORT${NC}"
    echo -e "${YELLOW}Please start the frontend with:${NC}"
    echo "  cd frontend && npm run dev"
    exit 1
else
    echo -e "${GREEN}✓${NC} Frontend is running on port $FRONTEND_PORT"
fi

echo ""

# Wait for services to be ready
wait_for_service "$BACKEND_URL/v1/health"
wait_for_service "$FRONTEND_URL"

echo ""
echo -e "${GREEN}=== Testing Backend API ===${NC}\n"

# Test Health Check
echo -e "${YELLOW}Testing Health Endpoint...${NC}"
test_endpoint "GET" "/v1/health"
health_response=$(curl -s "$BACKEND_URL/v1/health")
echo "  Response: $health_response"
echo ""

# Test Currency Endpoints
echo -e "${YELLOW}Testing Currency Endpoints...${NC}"
test_endpoint "GET" "/v1/currency/supported"
test_endpoint "GET" "/v1/currency/rates?base_currency=USD"
test_endpoint "GET" "/v1/currency/convert?amount=100&from_currency=USD&to_currency=CAD"
echo ""

# Test Transaction Endpoints
echo -e "${YELLOW}Testing Transaction Endpoints...${NC}"

# Get initial transactions count
initial_count=$(curl -s "$BACKEND_URL/v1/transactions/" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
echo "  Initial transaction count: $initial_count"

# Create a test transaction
echo -e "${YELLOW}Creating test transaction...${NC}"
transaction_data='{
  "description": "Test Transaction",
  "amount": 100.50,
  "currency": "USD",
  "type": "expense",
  "category": "Testing",
  "date": "2024-01-15T10:30:00",
  "account": "Test Account"
}'

test_endpoint "POST" "/v1/transactions/" "$transaction_data" 200
new_transaction=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d "$transaction_data" \
    "$BACKEND_URL/v1/transactions/")

transaction_id=$(echo "$new_transaction" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])" 2>/dev/null || echo "")
echo "  Created transaction ID: $transaction_id"

# Get all transactions
test_endpoint "GET" "/v1/transactions/"

# Get transaction by ID
if [ -n "$transaction_id" ]; then
    test_endpoint "GET" "/v1/transactions/$transaction_id"
fi

# Test currency conversion in transactions
test_endpoint "GET" "/v1/transactions/?currency=CAD"

# Delete test transaction
if [ -n "$transaction_id" ]; then
    echo -e "${YELLOW}Deleting test transaction...${NC}"
    test_endpoint "DELETE" "/v1/transactions/$transaction_id" "" 200
fi

echo ""

# Test Frontend
echo -e "${GREEN}=== Testing Frontend ===${NC}\n"

echo -e "${YELLOW}Testing Frontend Pages...${NC}"

pages=("/" "/transactions" "/portfolio" "/accounts" "/settings")
for page in "${pages[@]}"; do
    status_code=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL$page")
    if [ "$status_code" = "200" ]; then
        echo -e "${GREEN}✓${NC} Page $page - Status: $status_code"
    else
        echo -e "${RED}✗${NC} Page $page - Status: $status_code"
    fi
done

echo ""

# Test API Integration
echo -e "${YELLOW}Testing Frontend-Backend Integration...${NC}"
frontend_health=$(curl -s "$FRONTEND_URL" | grep -i "ledgerlight\|dashboard" > /dev/null && echo "OK" || echo "FAIL")
if [ "$frontend_health" = "OK" ]; then
    echo -e "${GREEN}✓${NC} Frontend loads successfully"
else
    echo -e "${RED}✗${NC} Frontend may not be loading correctly"
fi

echo ""

# Summary
echo -e "${GREEN}=== Test Summary ===${NC}\n"
echo -e "${GREEN}All tests completed!${NC}"
echo ""
echo "Backend API: $BACKEND_URL"
echo "Frontend: $FRONTEND_URL"
echo ""
echo -e "${YELLOW}To view API documentation, visit:${NC} $BACKEND_URL/docs"
echo -e "${YELLOW}To view interactive API docs, visit:${NC} $BACKEND_URL/redoc"

