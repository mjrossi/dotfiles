#!/bin/bash
# Run all dotfiles tests

set -e

echo "Running dotfiles tests..."
echo ""

python3 -m unittest discover tests -v

echo ""
echo "✓ All tests passed!"
