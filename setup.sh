#!/bin/bash
echo "Running migrations..."
python3 manage.py migrate --noinput
echo "Loading users..."
python3 manage.py loaddata users.json --ignorenonexistent
echo "Loading products..."
python3 manage.py loaddata products.json --ignorenonexistent
echo "Collecting static files..."
python3 manage.py collectstatic --noinput
echo "Setup complete!"
