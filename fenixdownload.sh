#!/usr/bin/env bash
# FenixDownload CLI - Multiplatform Launcher & Self-Bootstrapper
# Developed by Oswaldo Echeverría
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$DIR"

if command -v python3 >/dev/null 2>&1; then
    python3 bootstrap.py "$@"
elif command -v python >/dev/null 2>&1; then
    python bootstrap.py "$@"
else
    echo "[!] Error: Python no encontrado. Instala Python 3.12+ para ejecutar FenixDownload."
    exit 1
fi
