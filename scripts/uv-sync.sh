#!/bin/bash
set -e

echo "Syncing dependencies with uv..."
uv pip sync uv.lock

echo "Dependencies synced successfully!"
