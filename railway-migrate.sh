#!/bin/bash
# Railway post-deployment migration script
# Run this manually after deployment or set as a Railway deployment command

echo "Running database migrations..."
flask db upgrade

echo "Migrations completed successfully!"
