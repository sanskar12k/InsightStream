#!/bin/bash

# E-Commerce Scraper Development Starter Script

echo "==================================="
echo "E-Commerce Scraper - Development"
echo "==================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if MySQL is running
echo -e "${YELLOW}Checking MySQL...${NC}"
if pgrep -x "mysqld" > /dev/null; then
    echo -e "${GREEN}✓ MySQL is running${NC}"
else
    echo -e "${RED}✗ MySQL is not running. Please start MySQL first.${NC}"
    exit 1
fi

# Start backend
echo ""
echo -e "${YELLOW}Starting Backend Server...${NC}"
cd "$(dirname "$0")"
python app.py &
BACKEND_PID=$!
echo -e "${GREEN}✓ Backend started on http://localhost:8000 (PID: $BACKEND_PID)${NC}"

# Wait for backend to start
sleep 3

# Start frontend
echo ""
echo -e "${YELLOW}Starting Frontend Server...${NC}"
cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing frontend dependencies...${NC}"
    npm install
fi

npm run dev &
FRONTEND_PID=$!
echo -e "${GREEN}✓ Frontend started on http://localhost:3000 (PID: $FRONTEND_PID)${NC}"

echo ""
echo "==================================="
echo -e "${GREEN}Application is running!${NC}"
echo "==================================="
echo ""
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop all servers"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}Stopping servers...${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo -e "${GREEN}Servers stopped${NC}"
    exit 0
}

# Trap Ctrl+C
trap cleanup INT

# Wait for both processes
wait
