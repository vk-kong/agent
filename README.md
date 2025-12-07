# Local Docker Compose Agent

A lightweight agent that runs on your local machine to accept authenticated HTTP requests from a remote EC2 server and execute Docker Compose commands locally.

## Features

- 🔒 **Secure Authentication**: Token-based authentication for all API requests
- 🐳 **Docker Compose Management**: Start, stop, and check status of Docker containers
- 🌐 **HTTP API**: Simple REST API for remote control
- ⚙️ **Configurable**: YAML-based configuration
- 📝 **Logging**: Comprehensive logging for debugging and monitoring

## Use Case

This agent is designed for scenarios where you have:
- A web server running on EC2 where users can log in
- A need to trigger Docker Compose deployments on local machines
- Security requirements that prevent direct EC2-to-local Docker access

## Prerequisites

- Python 3.7 or higher
- Docker and Docker Compose installed on the local machine
- Network connectivity between EC2 server and local machine (with port forwarding if needed)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/vk-kong/agent.git
cd agent
```

2. Create a virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create configuration file:
```bash
cp config.example.yml config.yml
```

5. Generate a secure authentication token:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

6. Edit `config.yml` with your settings:
```yaml
server:
  host: "127.0.0.1"  # Use 0.0.0.0 to accept external connections
  port: 5050

auth:
  token: "your-generated-token-here"

docker:
  working_directory: "/path/to/your/docker-compose-directory"
  compose_command: "docker compose"

logging:
  level: "INFO"
  file: "agent.log"
```

## Usage

### Starting the Agent

```bash
python agent.py
```

The agent will start and listen on the configured host and port (default: http://localhost:5050).

### API Endpoints

#### 1. Health Check (No Authentication Required)

```bash
curl http://localhost:5050/health
```

Response:
```json
{
  "status": "healthy",
  "message": "Local Docker Compose Agent is running"
}
```

#### 2. Start Docker Compose

```bash
curl -X POST http://localhost:5050/docker/compose/up \
  -H "Authorization: Bearer your-token-here" \
  -H "Content-Type: application/json" \
  -d '{
    "detached": true,
    "build": false,
    "force_recreate": false
  }'
```

Response:
```json
{
  "success": true,
  "command": "docker compose up -d",
  "working_directory": "/path/to/docker-compose",
  "stdout": "...",
  "stderr": "",
  "return_code": 0
}
```

#### 3. Stop Docker Compose

```bash
curl -X POST http://localhost:5050/docker/compose/down \
  -H "Authorization: Bearer your-token-here" \
  -H "Content-Type: application/json" \
  -d '{
    "volumes": false,
    "remove_orphans": true
  }'
```

#### 4. Check Container Status

```bash
curl http://localhost:5050/docker/compose/status \
  -H "Authorization: Bearer your-token-here"
```

## EC2 Server Integration

To integrate with your EC2 server, you'll need to:

1. **Expose the agent to your network** (if EC2 needs to reach it):
   - Update `config.yml` to set `host: "0.0.0.0"`
   - Configure your firewall to allow incoming connections on port 5050
   - Consider using a reverse proxy (nginx) with HTTPS for production

2. **Set up port forwarding** (if behind NAT):
   - Configure your router to forward port 5050 to your local machine
   - Or use a tunneling service like ngrok for testing

3. **Make API calls from EC2**:

```python
import requests

AGENT_URL = "http://your-local-ip:5050"
AUTH_TOKEN = "your-secret-token"

headers = {
    "Authorization": f"Bearer {AUTH_TOKEN}",
    "Content-Type": "application/json"
}

# Start Docker Compose
response = requests.post(
    f"{AGENT_URL}/docker/compose/up",
    headers=headers,
    json={"detached": True, "build": False}
)

if response.status_code == 200:
    print("Docker Compose started successfully")
    print(response.json())
else:
    print(f"Error: {response.json()}")
```

## Security Considerations

⚠️ **Important Security Notes:**

1. **Token Security**: Keep your authentication token secret. Never commit it to version control.
2. **HTTPS**: For production use, put the agent behind a reverse proxy with HTTPS (e.g., nginx with Let's Encrypt).
3. **Firewall**: Only allow connections from trusted IP addresses (your EC2 server).
4. **Local Only**: By default, the agent listens on `127.0.0.1` (localhost only). Only change this if you understand the security implications.
5. **Network Security**: Consider using VPN or SSH tunneling instead of exposing the agent directly to the internet.

## Running as a Service

### Linux (systemd)

Create `/etc/systemd/system/docker-agent.service`:

```ini
[Unit]
Description=Local Docker Compose Agent
After=network.target docker.service

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/agent
ExecStart=/path/to/agent/venv/bin/python /path/to/agent/agent.py
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable docker-agent
sudo systemctl start docker-agent
sudo systemctl status docker-agent
```

### macOS (launchd)

Create `~/Library/LaunchAgents/com.dockeragent.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.dockeragent</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/agent/venv/bin/python</string>
        <string>/path/to/agent/agent.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>WorkingDirectory</key>
    <string>/path/to/agent</string>
</dict>
</plist>
```

Load the service:
```bash
launchctl load ~/Library/LaunchAgents/com.dockeragent.plist
```

## Troubleshooting

### Agent won't start
- Check that Python dependencies are installed: `pip install -r requirements.txt`
- Verify `config.yml` exists and is valid YAML
- Check that the configured port is not already in use

### Authentication fails
- Ensure the `Authorization` header is formatted correctly: `Bearer <token>`
- Verify the token in your request matches the token in `config.yml`

### Docker commands fail
- Verify Docker is installed and running: `docker --version`
- Check that the working directory in `config.yml` exists and contains `docker-compose.yml`
- Ensure the user running the agent has permission to execute Docker commands

### Cannot connect from EC2
- Verify the agent is listening on `0.0.0.0` instead of `127.0.0.1`
- Check firewall rules allow incoming connections on port 5050
- Confirm port forwarding is configured correctly (if behind NAT)

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-flask

# Run tests
pytest
```

## License

MIT License - Feel free to use and modify as needed.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.