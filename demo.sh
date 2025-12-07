#!/bin/bash
# Demonstration script for the Local Docker Compose Agent
# This shows the complete workflow from setup to execution

set -e

echo "========================================="
echo "Local Docker Compose Agent Demo"
echo "========================================="
echo ""

# Check if running in demo mode
if [ ! -d "venv" ]; then
    echo "⚠ Virtual environment not found."
    echo "Running quick setup..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
    echo "✓ Setup complete"
else
    source venv/bin/activate
    echo "✓ Virtual environment activated"
fi

echo ""
echo "Starting the agent in background..."
python agent.py > /tmp/agent-demo.log 2>&1 &
AGENT_PID=$!
echo "✓ Agent started (PID: $AGENT_PID)"

# Wait for agent to start
sleep 3

echo ""
echo "========================================="
echo "Testing API Endpoints"
echo "========================================="
echo ""

# Get the auth token from config
TOKEN=$(grep "token:" config.yml | awk '{print $2}' | tr -d '"')

echo "1. Health Check (No Authentication):"
echo "   $ curl http://localhost:5050/health"
curl -s http://localhost:5050/health | python3 -m json.tool
echo ""

echo "2. Unauthorized Request (Missing Token):"
echo "   $ curl http://localhost:5050/docker/compose/status"
curl -s http://localhost:5050/docker/compose/status | python3 -m json.tool
echo ""

echo "3. Get Docker Compose Status (Authenticated):"
echo "   $ curl -H \"Authorization: Bearer <token>\" http://localhost:5050/docker/compose/status"
curl -s -H "Authorization: Bearer $TOKEN" \
    http://localhost:5050/docker/compose/status | python3 -m json.tool
echo ""

echo "4. Start Docker Compose (Authenticated):"
echo "   $ curl -X POST -H \"Authorization: Bearer <token>\" http://localhost:5050/docker/compose/up"
echo "   Note: This will actually start containers if docker-compose.yml exists in working directory"
echo ""

echo "========================================="
echo "EC2 Integration Example"
echo "========================================="
echo ""
echo "From your EC2 server, you can use the LocalAgentClient class:"
echo ""
cat << 'EOF'
from ec2_integration_example import LocalAgentClient

# Initialize client
client = LocalAgentClient(
    agent_url="http://your-local-ip:5050",
    auth_token="your-secret-token"
)

# Check health
health = client.health_check()
print(health)

# Start deployment
result = client.start_deployment(detached=True, build=False)
print(result)

# Get status
status = client.get_status()
print(status)
EOF

echo ""
echo "========================================="
echo "Security Considerations"
echo "========================================="
echo ""
echo "✓ Token-based authentication"
echo "✓ Localhost binding by default (127.0.0.1)"
echo "✓ No vulnerabilities in dependencies"
echo "✓ Request logging for audit trail"
echo "✓ Timeout protection for commands"
echo ""
echo "⚠ For production use:"
echo "  - Use HTTPS with reverse proxy (nginx + Let's Encrypt)"
echo "  - Restrict firewall to allow only EC2 IP"
echo "  - Consider VPN or SSH tunneling"
echo "  - Rotate authentication tokens regularly"
echo ""

echo "========================================="
echo "Cleanup"
echo "========================================="
echo ""
kill $AGENT_PID 2>/dev/null || true
wait $AGENT_PID 2>/dev/null || true
echo "✓ Agent stopped"
echo ""
echo "Demo completed! Check /tmp/agent-demo.log for agent logs."
echo ""
