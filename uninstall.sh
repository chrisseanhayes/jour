#!/usr/bin/env sh
set -e

REMOVE_ALL_DATA=0

for arg in "$@"; do
    case $arg in
        --remove-all-data)
            REMOVE_ALL_DATA=1
            shift
            ;;
        *)
            echo "Unknown argument: $arg"
            echo "Usage: $0 [--remove-all-data]"
            exit 1
            ;;
    esac
done

echo "Uninstalling jour..."

if command -v pipx >/dev/null 2>&1; then
    pipx uninstall jour
else
    echo "Warning: pipx is not available. Cannot uninstall jour via pipx."
fi

if [ "$REMOVE_ALL_DATA" -eq 1 ]; then
    if [ -d "$HOME/.jour" ]; then
        echo "Removing all data in $HOME/.jour..."
        rm -rf "$HOME/.jour"
        echo "Data removed."
    else
        echo "No data found at $HOME/.jour."
    fi
else
    if [ -d "$HOME/.jour" ]; then
        echo "Note: User data in $HOME/.jour was not removed."
        echo "Run '$0 --remove-all-data' to remove it."
    fi
fi

echo "Uninstallation complete."
