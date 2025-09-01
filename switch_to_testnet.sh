#!/bin/bash

echo "🔄 SWITCHING TO TESTNET MODE - Safe Development"
echo "=" * 50

# Backup current environment
cp /app/backend/.env /app/backend/.env.current

# Switch to testnet configuration
cp /app/backend/.env.testnet /app/backend/.env

# Update supervisor to use regular server
cat > /etc/supervisor/conf.d/backend.conf << 'EOL'
[program:backend]
command=/root/.venv/bin/python -m uvicorn server:app --host 0.0.0.0 --port 8001 --reload
directory=/app/backend
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/backend.err.log
stdout_logfile=/var/log/supervisor/backend.out.log
environment=PATH="/root/.venv/bin",JAVA_HOME="/usr/lib/jvm/java-17-openjdk-arm64",MAINNET_MODE="false"
user=root
EOL

# Restart services
echo "Restarting backend with TESTNET configuration..."
sudo supervisorctl restart backend

echo "✅ Switched to TESTNET mode"
echo "💡 Safe for development - no real money costs"
echo ""
echo "To switch back to mainnet:"
echo "  ./switch_to_mainnet.sh"