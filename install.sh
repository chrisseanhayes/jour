#!/usr/bin/env sh
set -e

# Ensure pipx is available to install python applications cleanly
if ! command -v pipx >/dev/null 2>&1; then
    echo "pipx is required to install python applications cleanly without breaking system packages."
    echo "Attempting to install pipx via Homebrew..."
    if command -v brew >/dev/null 2>&1; then
        brew install pipx
        pipx ensurepath
        echo "pipx installed successfully."
    else
        echo "Homebrew is not installed. Please install pipx manually."
        exit 1
    fi
fi

echo "Installing jour using pipx..."
pipx install -e . --force

# Verify installation path
BIN_DIR="$HOME/.local/bin"
case ":$PATH:" in
    *":$BIN_DIR:"*)
        echo "Installation complete. Run 'jour' from anywhere."
        ;;
    *)
        echo "Installation complete."
        echo "Warning: $BIN_DIR is not currently in your \$PATH."
        echo "You may need to restart your terminal or add it to your shell rc file."
        echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
        ;;
esac
