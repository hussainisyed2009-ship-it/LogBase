#!/bin/bash
set -e

# Initialize database tables after deployment
cd /var/app/current

# Set FLASK_ENV so app knows it's production
export FLASK_ENV=production

# Find the venv and use it
VENV_PYTHON="$(find /var/app/venv -name python3 -type f | head -1)"
if [ -z "$VENV_PYTHON" ]; then
  VENV_PYTHON="/var/app/venv/*/bin/python"
fi

# Use the Python venv that EB set up
$VENV_PYTHON << 'EOF'
import sys
import os
os.environ['FLASK_ENV'] = 'production'
from website import create_app, db

try:
    app = create_app()
    with app.app_context():
        db.create_all()
        print("✓ Database tables initialized successfully")
except Exception as e:
    print(f"Error initializing database: {e}", file=sys.stderr)
    sys.exit(1)
EOF

# Fix permissions: Flask app runs as ec2-user, postdeploy runs as root
echo "✓ Fixing database permissions for ec2-user..."
chmod 666 /tmp/database.db 2>/dev/null || true
chown ec2-user:ec2-user /tmp/database.db 2>/dev/null || true
chmod 777 /tmp 2>/dev/null || true

echo "✓ Database ready and permissions fixed"




