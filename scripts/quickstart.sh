#!/bin/bash

# Quick start script for Cactus Trading Bot

set -e

echo "=================================="
echo "Cactus AI Auto Trader - Quick Start"
echo "=================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Create logs directory
echo "Creating logs directory..."
mkdir -p logs

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "=================================="
echo "Next Steps:"
echo "=================================="
echo ""
echo "1. Start databases (choose one):"
echo ""
echo "   Option A - Using Docker Compose (recommended):"
echo "   docker-compose up -d influxdb redis postgres"
echo ""
echo "   Option B - Start manually:"
echo "   docker run -d -p 8086:8086 influxdb:3.0"
echo "   docker run -d -p 6379:6379 redis:7-alpine"
echo "   docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres:15"
echo ""
echo "2. Configure environment:"
echo "   cp .env.example .env"
echo "   # Edit .env with your API keys"
echo ""
echo "3. Run system test:"
echo "   python main.py"
echo ""
echo "4. Run tests:"
echo "   pytest"
echo ""
echo "=================================="
echo "Done!"
echo "=================================="
