#!/usr/bin/env bash
# FenixDownload CLI - Multiplatform Launcher (Linux / macOS)
# Developed by Oswaldo Echeverría
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$DIR"

if command -v uv >/dev/null 2>&1; then
    uv run python -m fenixdownload.cli "$@"
elif [ -f ".venv/bin/python" ]; then
    .venv/bin/python -m fenixdownload.cli "$@"
else
    python3 -m fenixdownload.cli "$@"
fi
