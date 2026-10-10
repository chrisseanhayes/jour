#!/usr/bin/env sh
set -e

# Ensure pip is available and install package locally
pip3 install --user -e .

# Verify installation path
BIN_DIR="$HOME/.local/bin"
case ":$PATH:" in
    *":$BIN_DIR:"*)
        echo "Installation complete. Run 'jour' from anywhere."
        ;;
    *)
        echo "Warning: $BIN_DIR is not currently in your \$PATH."
        echo "Add the following to your shell rc file (~/.bashrc, ~/.zshrc, etc.):"
        echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
        ;;
esac
