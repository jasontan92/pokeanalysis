#!/bin/bash
#
# Setup script for Pokemon Listing Monitor
# Run this on your cloud server to set up the cron job
#

set -e

# Configuration
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
LOG_FILE="/var/log/pokeanalysis.log"

echo "=========================================="
echo "Pokemon Listing Monitor Setup"
echo "=========================================="
echo ""
echo "Project directory: $PROJECT_DIR"
echo ""

# Check Python version
echo "Checking Python..."
$PYTHON_BIN --version || {
    echo "ERROR: Python 3 not found. Please install Python 3.8+"
    exit 1
}

# Create virtual environment if it doesn't exist
if [ ! -d "$PROJECT_DIR/venv" ]; then
    echo "Creating virtual environment..."
    $PYTHON_BIN -m venv "$PROJECT_DIR/venv"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source "$PROJECT_DIR/venv/bin/activate"

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r "$PROJECT_DIR/requirements.txt"

# Check for .env file
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo ""
    echo "WARNING: .env file not found!"
    echo "Please copy .env.example to .env and fill in your credentials:"
    echo ""
    echo "  cp $PROJECT_DIR/.env.example $PROJECT_DIR/.env"
    echo "  nano $PROJECT_DIR/.env"
    echo ""
fi

# Create log file if it doesn't exist
if [ ! -f "$LOG_FILE" ]; then
    echo "Creating log file..."
    sudo touch "$LOG_FILE"
    sudo chmod 666 "$LOG_FILE"
fi

# Create cron job
echo ""
echo "Setting up cron job..."
CRON_CMD="*/30 * * * * cd $PROJECT_DIR && $PROJECT_DIR/venv/bin/python monitor.py >> $LOG_FILE 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "pokeanalysis.*monitor.py"; then
    echo "Cron job already exists. Updating..."
    # Remove old cron job
    crontab -l 2>/dev/null | grep -v "pokeanalysis.*monitor.py" | crontab -
fi

# Add new cron job
(crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -

echo ""
echo "=========================================="
echo "Setup complete!"
echo "=========================================="
echo ""
echo "The monitor will run every 30 minutes."
echo ""
echo "To test the monitor manually:"
echo "  cd $PROJECT_DIR"
echo "  source venv/bin/activate"
echo "  python monitor.py"
echo ""
echo "To view logs:"
echo "  tail -f $LOG_FILE"
echo ""
echo "To check cron jobs:"
echo "  crontab -l"
echo ""
echo "To remove the cron job:"
echo "  crontab -l | grep -v 'pokeanalysis.*monitor.py' | crontab -"
echo ""
