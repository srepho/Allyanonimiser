#!/bin/bash

# Install documentation dependencies if needed
if ! command -v mkdocs &> /dev/null; then
    echo "Installing MkDocs and dependencies..."
    pip install -r docs/requirements.txt
fi

# Build and serve the documentation
echo "Starting MkDocs server..."
mkdocs serve