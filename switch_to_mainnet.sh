#!/bin/bash

echo "🚨 SWITCHING TO MAINNET MODE - REAL MONEY TRANSACTIONS"
echo "=" * 60

# Backup current environment
cp /app/backend/.env /app/backend/.env.backup

# Switch to mainnet configuration
cp /app/backend/.env.mainnet /app/backend/.env

# Update supervisor to use mainnet server
cat > /etc/supervisor/conf.d/backend.conf << 'EOL'
[program:backend]
command=/root/.venv/bin/python -m uvicorn server_mainnet:app --host 0.0.0.0 --port 8001 --reload
directory=/app/backend
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/backend.err.log
stdout_logfile=/var/log/supervisor/backend.out.log
environment=PATH="/root/.venv/bin",JAVA_HOME="/usr/lib/jvm/java-17-openjdk-arm64",MAINNET_MODE="true",COST_WARNING_ENABLED="true"
user=root
EOL

# Restart services
echo "Restarting backend with MAINNET configuration..."
sudo supervisorctl restart backend

echo "✅ Switched to MAINNET mode"
echo "⚠️  WARNING: All transactions will now cost real HBAR!"
echo "⚠️  Account balance: ~75 ℏ (~$1,800 USD value)"
echo ""
echo "To switch back to testnet:"
echo "  ./switch_to_testnet.sh"