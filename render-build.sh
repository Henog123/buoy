#!/bin/bash
# Run database migrations after build
echo "🚀 Running database migrations..."
flask db upgrade
echo "✅ Migrations completed!"
