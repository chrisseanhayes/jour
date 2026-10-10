A standard `pyproject.toml` paired with an installation shell script sets up the package and creates the global executable symlink.

### 1. `pyproject.toml`

Place this in the project root directory alongside `jour_cli/`:

```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "jour-cli"
version = "0.1.0"
dependencies = [
    "PyYAML",
]
requires-python = ">=3.8"
description = "Minimal CLI Journal"

[project.scripts]
jour = "jour_cli.main:main"

[tool.setuptools.packages.find]
include = ["jour_cli*"]

```

### 2. `install.sh`

Place this build script in the project root to install the package in editable mode and link it to your user path:

```zsh
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

```

### Execution

Run the installer from your terminal:

```zsh
chmod +x install.sh
./install.sh

```