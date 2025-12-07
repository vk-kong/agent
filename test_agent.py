"""
Tests for the Local Docker Compose Agent

Run with: pytest test_agent.py
"""

import pytest
import yaml
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from agent import app, load_config


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def config_file():
    """Create a temporary config file for testing."""
    config_data = {
        'server': {
            'host': '127.0.0.1',
            'port': 5050
        },
        'auth': {
            'token': 'test-token-123'
        },
        'docker': {
            'working_directory': '/tmp/test-docker',
            'compose_command': 'docker compose'
        },
        'logging': {
            'level': 'INFO',
            'file': 'test.log'
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        yaml.dump(config_data, f)
        config_path = f.name
    
    yield config_path
    
    # Cleanup
    os.unlink(config_path)


def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'
    assert 'message' in data


def test_missing_auth_header(client, config_file):
    """Test that requests without auth header are rejected."""
    load_config(config_file)
    
    response = client.post('/docker/compose/up')
    assert response.status_code == 401
    data = response.get_json()
    assert 'error' in data


def test_invalid_auth_format(client, config_file):
    """Test that invalid auth format is rejected."""
    load_config(config_file)
    
    response = client.post(
        '/docker/compose/up',
        headers={'Authorization': 'InvalidFormat'}
    )
    assert response.status_code == 401
    data = response.get_json()
    assert 'error' in data


def test_invalid_token(client, config_file):
    """Test that invalid token is rejected."""
    load_config(config_file)
    
    response = client.post(
        '/docker/compose/up',
        headers={'Authorization': 'Bearer wrong-token'}
    )
    assert response.status_code == 401
    data = response.get_json()
    assert 'error' in data


def test_valid_auth(client, config_file):
    """Test that valid auth token is accepted."""
    load_config(config_file)
    
    # Create test directory
    os.makedirs('/tmp/test-docker', exist_ok=True)
    
    with patch('subprocess.run') as mock_run:
        # Mock successful docker compose up
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='Container started',
            stderr=''
        )
        
        response = client.post(
            '/docker/compose/up',
            headers={'Authorization': 'Bearer test-token-123'},
            json={'detached': True}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True


@patch('subprocess.run')
def test_docker_compose_up(mock_run, client, config_file):
    """Test docker compose up endpoint."""
    load_config(config_file)
    os.makedirs('/tmp/test-docker', exist_ok=True)
    
    # Mock successful execution
    mock_run.return_value = MagicMock(
        returncode=0,
        stdout='Starting containers...\nStarted',
        stderr=''
    )
    
    response = client.post(
        '/docker/compose/up',
        headers={'Authorization': 'Bearer test-token-123'},
        json={
            'detached': True,
            'build': False,
            'force_recreate': False
        }
    )
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'docker compose up -d' in data['command']
    
    # Verify subprocess was called correctly
    mock_run.assert_called_once()
    call_args = mock_run.call_args
    assert 'docker' in call_args[0][0]
    assert 'compose' in call_args[0][0]
    assert 'up' in call_args[0][0]
    assert '-d' in call_args[0][0]


@patch('subprocess.run')
def test_docker_compose_down(mock_run, client, config_file):
    """Test docker compose down endpoint."""
    load_config(config_file)
    os.makedirs('/tmp/test-docker', exist_ok=True)
    
    # Mock successful execution
    mock_run.return_value = MagicMock(
        returncode=0,
        stdout='Stopping containers...\nStopped',
        stderr=''
    )
    
    response = client.post(
        '/docker/compose/down',
        headers={'Authorization': 'Bearer test-token-123'},
        json={
            'volumes': False,
            'remove_orphans': True
        }
    )
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'docker compose down' in data['command']
    
    # Verify subprocess was called correctly
    mock_run.assert_called_once()
    call_args = mock_run.call_args
    assert 'docker' in call_args[0][0]
    assert 'compose' in call_args[0][0]
    assert 'down' in call_args[0][0]


@patch('subprocess.run')
def test_docker_compose_status(mock_run, client, config_file):
    """Test docker compose status endpoint."""
    load_config(config_file)
    os.makedirs('/tmp/test-docker', exist_ok=True)
    
    # Mock successful execution
    mock_run.return_value = MagicMock(
        returncode=0,
        stdout='{"Name": "test_container", "State": "running"}',
        stderr=''
    )
    
    response = client.get(
        '/docker/compose/status',
        headers={'Authorization': 'Bearer test-token-123'}
    )
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    
    # Verify subprocess was called correctly
    mock_run.assert_called_once()
    call_args = mock_run.call_args
    assert 'docker' in call_args[0][0]
    assert 'compose' in call_args[0][0]
    assert 'ps' in call_args[0][0]


@patch('subprocess.run')
def test_docker_compose_failure(mock_run, client, config_file):
    """Test handling of docker compose failures."""
    load_config(config_file)
    os.makedirs('/tmp/test-docker', exist_ok=True)
    
    # Mock failed execution
    mock_run.return_value = MagicMock(
        returncode=1,
        stdout='',
        stderr='Error: Something went wrong'
    )
    
    response = client.post(
        '/docker/compose/up',
        headers={'Authorization': 'Bearer test-token-123'},
        json={'detached': True}
    )
    
    assert response.status_code == 500
    data = response.get_json()
    assert data['success'] is False
    assert data['return_code'] == 1


def test_load_config_file_not_found():
    """Test that missing config file exits gracefully."""
    with pytest.raises(SystemExit):
        load_config('nonexistent-config.yml')


def test_load_config_success(config_file):
    """Test successful config loading."""
    config = load_config(config_file)
    assert config is not None
    assert 'server' in config
    assert 'auth' in config
    assert 'docker' in config
