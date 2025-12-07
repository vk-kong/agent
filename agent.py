#!/usr/bin/env python3
"""
Local Agent for Docker Compose Management

This agent runs on a local machine and exposes an HTTP API that allows
authenticated requests from a remote EC2 server to trigger Docker Compose
commands locally.
"""

import os
import sys
import logging
import subprocess
import yaml
from pathlib import Path
from functools import wraps
from flask import Flask, request, jsonify

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Global configuration
config = {}


def load_config(config_path='config.yml'):
    """Load configuration from YAML file."""
    global config
    try:
        if not Path(config_path).exists():
            logger.error(f"Configuration file not found: {config_path}")
            logger.info("Please copy config.example.yml to config.yml and update it")
            sys.exit(1)
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Set logging level from config
        log_level = config.get('logging', {}).get('level', 'INFO')
        logging.getLogger().setLevel(getattr(logging, log_level))
        
        logger.info("Configuration loaded successfully")
        return config
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        sys.exit(1)


def require_auth(f):
    """Decorator to require authentication token."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            logger.warning(f"Unauthorized request from {request.remote_addr}: Missing Authorization header")
            return jsonify({'error': 'Missing authorization header'}), 401
        
        # Expected format: "Bearer <token>"
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            logger.warning(f"Unauthorized request from {request.remote_addr}: Invalid Authorization format")
            return jsonify({'error': 'Invalid authorization format. Use: Bearer <token>'}), 401
        
        token = parts[1]
        expected_token = config.get('auth', {}).get('token')
        
        if not expected_token:
            logger.error("No auth token configured in config.yml")
            return jsonify({'error': 'Server configuration error'}), 500
        
        if token != expected_token:
            logger.warning(f"Unauthorized request from {request.remote_addr}: Invalid token")
            return jsonify({'error': 'Invalid authorization token'}), 401
        
        logger.info(f"Authenticated request from {request.remote_addr}")
        return f(*args, **kwargs)
    
    return decorated_function


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint - no authentication required."""
    return jsonify({
        'status': 'healthy',
        'message': 'Local Docker Compose Agent is running'
    }), 200


@app.route('/docker/compose/up', methods=['POST'])
@require_auth
def docker_compose_up():
    """
    Trigger docker compose up command.
    
    Request body (optional):
        {
            "detached": true,       # Run in detached mode (default: true)
            "build": false,         # Build images before starting (default: false)
            "force_recreate": false # Recreate containers (default: false)
        }
    """
    try:
        data = request.get_json() or {}
        
        # Get Docker configuration
        docker_config = config.get('docker', {})
        working_dir = docker_config.get('working_directory')
        compose_command = docker_config.get('compose_command', 'docker compose')
        
        if not working_dir:
            logger.error("Docker working directory not configured")
            return jsonify({'error': 'Docker working directory not configured'}), 500
        
        if not Path(working_dir).exists():
            logger.error(f"Docker working directory does not exist: {working_dir}")
            return jsonify({'error': f'Working directory does not exist: {working_dir}'}), 500
        
        # Build command
        cmd = compose_command.split()
        cmd.append('up')
        
        # Add options
        if data.get('detached', True):
            cmd.append('-d')
        
        if data.get('build', False):
            cmd.append('--build')
        
        if data.get('force_recreate', False):
            cmd.append('--force-recreate')
        
        logger.info(f"Executing command: {' '.join(cmd)} in {working_dir}")
        
        # Execute command
        result = subprocess.run(
            cmd,
            cwd=working_dir,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        response = {
            'success': result.returncode == 0,
            'command': ' '.join(cmd),
            'working_directory': working_dir,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'return_code': result.returncode
        }
        
        if result.returncode == 0:
            logger.info("Docker Compose up executed successfully")
            return jsonify(response), 200
        else:
            logger.error(f"Docker Compose up failed with code {result.returncode}")
            return jsonify(response), 500
            
    except subprocess.TimeoutExpired:
        logger.error("Docker Compose command timed out")
        return jsonify({'error': 'Command execution timed out'}), 500
    except Exception as e:
        logger.error(f"Error executing docker compose up: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/docker/compose/down', methods=['POST'])
@require_auth
def docker_compose_down():
    """
    Trigger docker compose down command.
    
    Request body (optional):
        {
            "volumes": false,  # Remove volumes (default: false)
            "remove_orphans": true  # Remove orphans (default: true)
        }
    """
    try:
        data = request.get_json() or {}
        
        # Get Docker configuration
        docker_config = config.get('docker', {})
        working_dir = docker_config.get('working_directory')
        compose_command = docker_config.get('compose_command', 'docker compose')
        
        if not working_dir:
            logger.error("Docker working directory not configured")
            return jsonify({'error': 'Docker working directory not configured'}), 500
        
        # Build command
        cmd = compose_command.split()
        cmd.append('down')
        
        # Add options
        if data.get('volumes', False):
            cmd.append('--volumes')
        
        if data.get('remove_orphans', True):
            cmd.append('--remove-orphans')
        
        logger.info(f"Executing command: {' '.join(cmd)} in {working_dir}")
        
        # Execute command
        result = subprocess.run(
            cmd,
            cwd=working_dir,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        response = {
            'success': result.returncode == 0,
            'command': ' '.join(cmd),
            'working_directory': working_dir,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'return_code': result.returncode
        }
        
        if result.returncode == 0:
            logger.info("Docker Compose down executed successfully")
            return jsonify(response), 200
        else:
            logger.error(f"Docker Compose down failed with code {result.returncode}")
            return jsonify(response), 500
            
    except subprocess.TimeoutExpired:
        logger.error("Docker Compose command timed out")
        return jsonify({'error': 'Command execution timed out'}), 500
    except Exception as e:
        logger.error(f"Error executing docker compose down: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/docker/compose/status', methods=['GET'])
@require_auth
def docker_compose_status():
    """Get status of running containers."""
    try:
        # Get Docker configuration
        docker_config = config.get('docker', {})
        working_dir = docker_config.get('working_directory')
        compose_command = docker_config.get('compose_command', 'docker compose')
        
        if not working_dir:
            logger.error("Docker working directory not configured")
            return jsonify({'error': 'Docker working directory not configured'}), 500
        
        # Build command
        cmd = compose_command.split()
        cmd.extend(['ps', '--format', 'json'])
        
        logger.info(f"Executing command: {' '.join(cmd)} in {working_dir}")
        
        # Execute command
        result = subprocess.run(
            cmd,
            cwd=working_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        response = {
            'success': result.returncode == 0,
            'command': ' '.join(cmd),
            'working_directory': working_dir,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'return_code': result.returncode
        }
        
        if result.returncode == 0:
            logger.info("Docker Compose status retrieved successfully")
            return jsonify(response), 200
        else:
            logger.error(f"Docker Compose status failed with code {result.returncode}")
            return jsonify(response), 500
            
    except subprocess.TimeoutExpired:
        logger.error("Docker Compose command timed out")
        return jsonify({'error': 'Command execution timed out'}), 500
    except Exception as e:
        logger.error(f"Error getting docker compose status: {e}")
        return jsonify({'error': str(e)}), 500


def main():
    """Main entry point for the agent."""
    # Load configuration
    load_config()
    
    # Get server configuration
    server_config = config.get('server', {})
    host = server_config.get('host', '127.0.0.1')
    port = server_config.get('port', 5050)
    
    logger.info(f"Starting Local Docker Compose Agent on {host}:{port}")
    logger.info("Press Ctrl+C to stop")
    
    # Run Flask app
    app.run(
        host=host,
        port=port,
        debug=False
    )


if __name__ == '__main__':
    main()
