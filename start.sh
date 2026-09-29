#!/usr/bin/env bash
# One command for students: installs on the first run (or after requirements change), then opens the Guided Mission.
# Usage: ./start.sh            (Guided Mission)
#        ./start.sh --full     (free-play dashboard)
set -e
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
  echo "First run: setting up (about a minute)..."
  python3 -m venv .venv || { rm -rf .venv; echo "Python's venv module is missing. On Ubuntu run: sudo apt-get install -y python3-venv"; exit 1; }
fi
if [ ! -f .venv/.installed ] || [ requirements.txt -nt .venv/.installed ]; then
  .venv/bin/python -m pip install --quiet --disable-pip-version-check -r requirements.txt
  touch .venv/.installed
fi
exec .venv/bin/python launch.py "$@"
