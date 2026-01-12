#!/bin/bash
# Setup script for adversarial-strategy plugin
# Creates a virtual environment and installs dependencies

set -e

CONFIG_DIR="$HOME/.config/adversarial-strategy"
VENV_DIR="$CONFIG_DIR/venv"

echo "Setting up adversarial-strategy plugin..."

# Create config directory if needed
mkdir -p "$CONFIG_DIR"

# Create virtual environment
if [ -d "$VENV_DIR" ]; then
    echo "Virtual environment already exists at $VENV_DIR"
else
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# Install litellm
echo "Installing litellm..."
"$VENV_DIR/bin/pip" install --quiet --upgrade litellm

echo ""
echo "Setup complete!"
echo ""
echo "Python path for debate.py: $VENV_DIR/bin/python3"
echo ""
echo "Next steps:"
echo "  1. Configure API keys in $CONFIG_DIR/keys.json:"
echo '     {"OPENAI_API_KEY": "sk-...", "ANTHROPIC_API_KEY": "sk-ant-..."}'
echo "  2. chmod 600 $CONFIG_DIR/keys.json"
echo ""
