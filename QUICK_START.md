# Quick Reference Guide

## Setup (One-time)

```bash
# Clone and setup
git clone https://github.com/vk-kong/agent.git
cd agent
./setup.sh

# Edit config.yml with your settings
nano config.yml
```

## Starting the Agent

```bash
# Option 1: Using start script
./start.sh

# Option 2: Manual start
source venv/bin/activate
python agent.py
```

## API Endpoints

### Health Check (No Auth)
```bash
curl http://localhost:5050/health
```

### Start Deployment
```bash
curl -X POST http://localhost:5050/docker/compose/up \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"detached": true, "build": false}'
```

### Stop Deployment
```bash
curl -X POST http://localhost:5050/docker/compose/down \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"volumes": false}'
```

### Get Status
```bash
curl http://localhost:5050/docker/compose/status \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## EC2 Integration (Python)

```python
from ec2_integration_example import LocalAgentClient

client = LocalAgentClient(
    agent_url="http://192.168.1.100:5050",
    auth_token="your-secret-token"
)

# Start deployment
result = client.start_deployment(detached=True, build=False)
print(result)

# Get status
status = client.get_status()
print(status)

# Stop deployment
stop_result = client.stop_deployment()
print(stop_result)
```

## Configuration File Structure

```yaml
server:
  host: "127.0.0.1"  # or "0.0.0.0" for external access
  port: 5050

auth:
  token: "your-secret-token-here"

docker:
  working_directory: "/path/to/docker-compose-dir"
  compose_command: "docker compose"

logging:
  level: "INFO"
  file: "agent.log"
```

## Generating Secure Token

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Running as Service (Linux)

```bash
# Create service file
sudo nano /etc/systemd/system/docker-agent.service

# Enable and start
sudo systemctl enable docker-agent
sudo systemctl start docker-agent
sudo systemctl status docker-agent
```

## Troubleshooting

### Port already in use
```bash
# Find process using port 5050
sudo lsof -i :5050
# or
sudo netstat -tlnp | grep 5050

# Kill the process
kill <PID>
```

### Docker permission denied
```bash
# Add user to docker group
sudo usermod -aG docker $USER
# Log out and back in
```

### Cannot connect from EC2
1. Change host to "0.0.0.0" in config.yml
2. Configure firewall: `sudo ufw allow 5050`
3. Check port forwarding if behind router

## Security Checklist

- [ ] Use strong, randomly generated token
- [ ] Keep token secret (not in version control)
- [ ] Use HTTPS in production (nginx reverse proxy)
- [ ] Restrict firewall to EC2 IP only
- [ ] Consider VPN or SSH tunnel
- [ ] Rotate tokens regularly
- [ ] Monitor logs for suspicious activity

## Demo

```bash
./demo.sh
```

## Testing

```bash
source venv/bin/activate
pytest test_agent.py -v
```

## Support

See README.md for detailed documentation and examples.
