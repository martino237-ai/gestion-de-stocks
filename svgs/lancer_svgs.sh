#!/bin/bash
echo "=== SVGS - Lancement ==="
cd "$(dirname "$0")"
pip install mysql-connector-python -q 2>/dev/null || pip install mysql-connector-python --break-system-packages -q 2>/dev/null
python3 main.py
