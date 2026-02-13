#!/bin/bash
set -e

echo "Updating dependencies with uv..."

# Compile requirements.txt to uv.lock
uv pip compile requirements.txt --output-file=uv.lock

echo "Dependencies updated successfully!"
echo "Run 'uv pip sync uv.lock' to apply the changes to your environment."
