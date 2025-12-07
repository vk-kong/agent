#!/usr/bin/env python3
"""
Example EC2 Server Integration Script

This script demonstrates how to integrate the local agent with your EC2 web server.
You can use this as a starting point for your actual implementation.
"""

import requests
import os
from typing import Dict, Optional


class LocalAgentClient:
    """Client for communicating with the local Docker Compose agent."""
    
    def __init__(self, agent_url: str, auth_token: str):
        """
        Initialize the client.
        
        Args:
            agent_url: Base URL of the local agent (e.g., "http://192.168.1.100:5050")
            auth_token: Authentication token configured in the agent
        """
        self.agent_url = agent_url.rstrip('/')
        self.headers = {
            'Authorization': f'Bearer {auth_token}',
            'Content-Type': 'application/json'
        }
    
    def health_check(self) -> Dict:
        """
        Check if the agent is healthy and reachable.
        
        Returns:
            Response dictionary with status information
        """
        try:
            response = requests.get(
                f'{self.agent_url}/health',
                timeout=5
            )
            response.raise_for_status()
            return {
                'success': True,
                'data': response.json()
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def start_deployment(
        self,
        detached: bool = True,
        build: bool = False,
        force_recreate: bool = False
    ) -> Dict:
        """
        Start Docker Compose deployment on the local machine.
        
        Args:
            detached: Run containers in detached mode
            build: Build images before starting
            force_recreate: Recreate containers even if config hasn't changed
            
        Returns:
            Response dictionary with deployment status
        """
        try:
            response = requests.post(
                f'{self.agent_url}/docker/compose/up',
                headers=self.headers,
                json={
                    'detached': detached,
                    'build': build,
                    'force_recreate': force_recreate
                },
                timeout=300  # 5 minutes
            )
            
            data = response.json()
            
            return {
                'success': response.status_code == 200,
                'status_code': response.status_code,
                'data': data
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def stop_deployment(
        self,
        volumes: bool = False,
        remove_orphans: bool = True
    ) -> Dict:
        """
        Stop Docker Compose deployment on the local machine.
        
        Args:
            volumes: Remove named volumes
            remove_orphans: Remove containers for services not in compose file
            
        Returns:
            Response dictionary with status
        """
        try:
            response = requests.post(
                f'{self.agent_url}/docker/compose/down',
                headers=self.headers,
                json={
                    'volumes': volumes,
                    'remove_orphans': remove_orphans
                },
                timeout=300  # 5 minutes
            )
            
            data = response.json()
            
            return {
                'success': response.status_code == 200,
                'status_code': response.status_code,
                'data': data
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_status(self) -> Dict:
        """
        Get status of running containers.
        
        Returns:
            Response dictionary with container status
        """
        try:
            response = requests.get(
                f'{self.agent_url}/docker/compose/status',
                headers=self.headers,
                timeout=30
            )
            
            data = response.json()
            
            return {
                'success': response.status_code == 200,
                'status_code': response.status_code,
                'data': data
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e)
            }


# Example Flask integration (if your EC2 server uses Flask)
def example_flask_integration():
    """
    Example of how to integrate with a Flask web application on EC2.
    """
    from flask import Flask, request, jsonify
    
    app = Flask(__name__)
    
    # Configuration - should be stored securely (environment variables, secrets manager, etc.)
    AGENT_URL = os.getenv('LOCAL_AGENT_URL', 'http://192.168.1.100:5050')
    AGENT_TOKEN = os.getenv('LOCAL_AGENT_TOKEN', 'your-secret-token')
    
    # Initialize client
    agent_client = LocalAgentClient(AGENT_URL, AGENT_TOKEN)
    
    @app.route('/api/deploy/start', methods=['POST'])
    def start_deployment():
        """API endpoint to trigger local deployment."""
        # Add your own authentication/authorization here
        # For example, check if user is logged in and has permissions
        
        data = request.get_json() or {}
        
        result = agent_client.start_deployment(
            detached=data.get('detached', True),
            build=data.get('build', False),
            force_recreate=data.get('force_recreate', False)
        )
        
        if result['success']:
            return jsonify({
                'message': 'Deployment started successfully',
                'details': result['data']
            }), 200
        else:
            return jsonify({
                'message': 'Failed to start deployment',
                'error': result.get('error') or result.get('data', {}).get('error')
            }), 500
    
    @app.route('/api/deploy/stop', methods=['POST'])
    def stop_deployment():
        """API endpoint to stop local deployment."""
        # Add your own authentication/authorization here
        
        data = request.get_json() or {}
        
        result = agent_client.stop_deployment(
            volumes=data.get('volumes', False),
            remove_orphans=data.get('remove_orphans', True)
        )
        
        if result['success']:
            return jsonify({
                'message': 'Deployment stopped successfully',
                'details': result['data']
            }), 200
        else:
            return jsonify({
                'message': 'Failed to stop deployment',
                'error': result.get('error') or result.get('data', {}).get('error')
            }), 500
    
    @app.route('/api/deploy/status', methods=['GET'])
    def get_status():
        """API endpoint to get deployment status."""
        # Add your own authentication/authorization here
        
        result = agent_client.get_status()
        
        if result['success']:
            return jsonify({
                'message': 'Status retrieved successfully',
                'details': result['data']
            }), 200
        else:
            return jsonify({
                'message': 'Failed to get status',
                'error': result.get('error') or result.get('data', {}).get('error')
            }), 500
    
    return app


# Example usage
if __name__ == '__main__':
    # Configure your agent connection
    AGENT_URL = 'http://192.168.1.100:5050'  # Replace with your local machine's IP
    AGENT_TOKEN = 'your-secret-token-here'   # Replace with your actual token
    
    # Create client
    client = LocalAgentClient(AGENT_URL, AGENT_TOKEN)
    
    # Test health check
    print("Testing health check...")
    health = client.health_check()
    print(f"Health check result: {health}")
    
    if health['success']:
        # Start deployment
        print("\nStarting deployment...")
        start_result = client.start_deployment(detached=True, build=False)
        print(f"Start result: {start_result}")
        
        # Get status
        print("\nGetting status...")
        status_result = client.get_status()
        print(f"Status result: {status_result}")
        
        # Stop deployment (commented out - uncomment if you want to test)
        # print("\nStopping deployment...")
        # stop_result = client.stop_deployment()
        # print(f"Stop result: {stop_result}")
    else:
        print("Agent is not reachable. Please check the connection.")
