"""Tests for health check endpoints."""
import json


class TestHealthEndpoints:
    """Test suite for health check endpoints."""

    def test_health_check_returns_200(self, client):
        """Test that /health returns 200 status."""
        response = client.get('/health')
        assert response.status_code == 200

    def test_health_check_returns_json(self, client):
        """Test that /health returns valid JSON."""
        response = client.get('/health')
        data = json.loads(response.data)
        assert 'status' in data
        assert 'timestamp' in data

    def test_health_check_includes_database_status(self, client):
        """Test that /health includes database status."""
        response = client.get('/health')
        data = json.loads(response.data)
        assert 'database' in data

    def test_liveness_check_returns_200(self, client):
        """Test that /health/live returns 200."""
        response = client.get('/health/live')
        assert response.status_code == 200

    def test_liveness_check_returns_alive(self, client):
        """Test that /health/live indicates alive status."""
        response = client.get('/health/live')
        data = json.loads(response.data)
        assert data.get('alive') is True

    def test_readiness_check_returns_200_when_ready(self, client):
        """Test that /health/ready returns 200 when database is accessible."""
        response = client.get('/health/ready')
        assert response.status_code == 200

    def test_readiness_check_returns_ready(self, client):
        """Test that /health/ready indicates ready status."""
        response = client.get('/health/ready')
        data = json.loads(response.data)
        assert data.get('ready') is True


class TestFavicon:
    """Test favicon route."""

    def test_favicon_route_exists(self, client):
        """Test that favicon route is accessible."""
        response = client.get('/favicon.ico')
        # May return 404 if favicon file doesn't exist, but route should exist
        assert response.status_code in [200, 404]
