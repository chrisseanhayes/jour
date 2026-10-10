#!/usr/bin/env zsh
set -e

# Ensure pip is available and install package locally
pip3 install --user -e .

# Verify installation path
BIN_DIR="$HOME/.local/bin"
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo "Warning: $BIN_DIR is not currently in your \$PATH."
    echo "Add 'export PATH=\"\$HOME/.local/bin:\$PATH\"' to your ~/.zshrc file."
else
    echo "Installation complete. Run 'jour' from anywhere."
fi
