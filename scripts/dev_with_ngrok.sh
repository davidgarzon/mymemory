#!/bin/bash

# Development script with ngrok integration for Telegram webhooks
# This script starts ngrok, exposes the local backend, and optionally registers the Telegram webhook

set -e

NGROK_PORT=8000
NGROK_API_URL="http://127.0.0.1:4040/api/tunnels"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting development environment with ngrok...${NC}"

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo -e "${RED}❌ Error: ngrok is not installed${NC}"
    echo -e "${YELLOW}Install it with: brew install ngrok${NC}"
    echo -e "${YELLOW}Or download from: https://ngrok.com/download${NC}"
    exit 1
fi

# Check if ngrok is already running
if pgrep -x "ngrok" > /dev/null; then
    echo -e "${YELLOW}⚠️  ngrok is already running. Killing existing ngrok processes...${NC}"
    pkill -x ngrok || true
    sleep 2
fi

# Start ngrok in background
echo -e "${BLUE}Starting ngrok on port ${NGROK_PORT}...${NC}"
ngrok http $NGROK_PORT --log=stdout > /tmp/ngrok.log 2>&1 &
NGROK_PID=$!

# Wait for ngrok to start
echo -e "${BLUE}Waiting for ngrok to start...${NC}"
sleep 3

# Check if ngrok started successfully
if ! kill -0 $NGROK_PID 2>/dev/null; then
    echo -e "${RED}❌ Error: Failed to start ngrok${NC}"
    echo -e "${YELLOW}Check /tmp/ngrok.log for errors${NC}"
    exit 1
fi

# Get public URL from ngrok API
echo -e "${BLUE}Fetching public URL from ngrok...${NC}"
MAX_RETRIES=10
RETRY_COUNT=0
PUBLIC_URL=""

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    sleep 2
    
    # Try to get the public URL from ngrok API
    TUNNELS_RESPONSE=$(curl -s $NGROK_API_URL 2>/dev/null || echo "")
    
    if [ ! -z "$TUNNELS_RESPONSE" ]; then
        # Extract HTTPS URL (prefer HTTPS over HTTP)
        PUBLIC_URL=$(echo "$TUNNELS_RESPONSE" | grep -o '"public_url":"https://[^"]*"' | head -1 | cut -d'"' -f4)
        
        if [ -z "$PUBLIC_URL" ]; then
            # Fallback to HTTP if HTTPS not available
            PUBLIC_URL=$(echo "$TUNNELS_RESPONSE" | grep -o '"public_url":"http://[^"]*"' | head -1 | cut -d'"' -f4)
        fi
        
        if [ ! -z "$PUBLIC_URL" ]; then
            break
        fi
    fi
    
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo -e "${YELLOW}Retrying... (${RETRY_COUNT}/${MAX_RETRIES})${NC}"
done

if [ -z "$PUBLIC_URL" ]; then
    echo -e "${RED}❌ Error: Could not get public URL from ngrok${NC}"
    echo -e "${YELLOW}Check ngrok status: curl ${NGROK_API_URL}${NC}"
    kill $NGROK_PID 2>/dev/null || true
    exit 1
fi

echo -e "${GREEN}✅ ngrok is running!${NC}"
echo -e "${GREEN}Public URL: ${PUBLIC_URL}${NC}"

# Export PUBLIC_URL for docker compose
export PUBLIC_URL

# Start docker compose
echo -e "${BLUE}Starting docker compose...${NC}"
docker compose up -d

# Wait for services to be ready
echo -e "${BLUE}Waiting for services to start...${NC}"
sleep 5

# Show webhook endpoint
WEBHOOK_URL="${PUBLIC_URL}/api/v1/telegram/webhook"
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}🎉 Development environment is ready!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}Public URL (ngrok):${NC} ${GREEN}${PUBLIC_URL}${NC}"
echo -e "${BLUE}Webhook endpoint:${NC}  ${GREEN}${WEBHOOK_URL}${NC}"
echo ""
echo -e "${YELLOW}To register the Telegram webhook, run:${NC}"
echo -e "${GREEN}curl -X POST \"http://localhost:8000/api/v1/telegram/webhook/setup?public_url=${PUBLIC_URL}\"${NC}"
echo ""
echo -e "${BLUE}Or use this (PUBLIC_URL is already exported):${NC}"
echo -e "${GREEN}curl -X POST \"http://localhost:8000/api/v1/telegram/webhook/setup\"${NC}"
echo ""
echo -e "${YELLOW}Note: Keep this terminal open. Press Ctrl+C to stop ngrok and docker compose.${NC}"
echo ""

# Trap Ctrl+C to cleanup
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down...${NC}"
    echo -e "${BLUE}Stopping docker compose...${NC}"
    docker compose down
    echo -e "${BLUE}Stopping ngrok...${NC}"
    kill $NGROK_PID 2>/dev/null || true
    echo -e "${GREEN}✅ Cleanup complete${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Keep script running
echo -e "${BLUE}Watching docker compose logs (press Ctrl+C to stop)...${NC}"
docker compose logs -f
