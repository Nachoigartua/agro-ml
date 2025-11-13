#!/bin/sh
# Ensure dependencies exist before starting Angular dev server.
set -eu

LOCKFILE="/app/package-lock.json"
STAMP="/app/node_modules/.package-lock.json"

if [ ! -d /app/node_modules ] || [ ! -f "$STAMP" ] || ! cmp -s "$LOCKFILE" "$STAMP"; then
    echo "Installing frontend dependencies..."
    npm install
    cp "$LOCKFILE" "$STAMP"
else
    echo "Using cached node_modules (dependencies already up to date)."
fi

exec "$@"
