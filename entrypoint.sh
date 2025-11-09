#!/bin/sh
set -e

# Simple health echo
echo "[Michelangelo] Starting bot..."

# Verify token
if [ -z "$discord_token" ]; then
  echo "ERROR: discord_token env var not set" >&2
  exit 1
fi

exec python main.py
