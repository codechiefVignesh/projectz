#!/bin/bash

# Build script for Vercel
echo "Building static files..."
py -3.10 -m pip install -r requirements.txt
py -3.10 manage.py collectstatic --noinput --clear