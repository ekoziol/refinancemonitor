"""API contract tests for calculator endpoints."""
import pytest
from refi_monitor import init_app


@pytest.fixture
def app():
    """Create application for testing."""
    app = init_app()
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


class TestHealthEndpoint:
    """Tests for /api/health endpoint."""

    def test_health_returns_200(self, client):
        """Health endpoint returns 200 OK."""
        response = client.get('/api/health')
        assert response.status_code == 200

    def test_health_returns_json(self, client):
        """Health endpoint returns JSON."""
        response = client.get('/api/health')
        data = response.get_json()
        assert data['status'] == 'healthy'
        assert data['service'] == 'refi_alert_api'


class TestMonthlyPaymentEndpoint:
    """Tests for /api/calculator/monthly-payment endpoint."""

    def test_valid_request_returns_200(self, client):
        """Valid request returns 200."""
        response = client.post('/api/calculator/monthly-payment', json={
            'principal': 200000,
            'rate': 0.065,
            'term': 360
        })
        assert response.status_code == 200
        data = response.get_json()
        assert 'monthly_payment' in data
        assert data['monthly_payment'] > 0

    def test_missing_principal_returns_400(self, client):
        """Missing principal returns 400."""
        response = client.post('/api/calculator/monthly-payment', json={
            'rate': 0.065,
            'term': 360
        })
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'principal' in str(data.get('details', {}))

    def test_missing_rate_returns_400(self, client):
        """Missing rate returns 400."""
        response = client.post('/api/calculator/monthly-payment', json={
            'principal': 200000,
            'term': 360
        })
        assert response.status_code == 400

    def test_missing_term_returns_400(self, client):
        """Missing term returns 400."""
        response = client.post('/api/calculator/monthly-payment', json={
            'principal': 200000,
            'rate': 0.065
        })
        assert response.status_code == 400

    def test_negative_principal_returns_400(self, client):
        """Negative principal returns 400."""
        response = client.post('/api/calculator/monthly-payment', json={
            'principal': -100000,
            'rate': 0.065,
            'term': 360
        })
        assert response.status_code == 400

    def test_rate_above_1_returns_400(self, client):
        """Rate >= 1 returns 400."""
        response = client.post('/api/calculator/monthly-payment', json={
            'principal': 200000,
            'rate': 1.5,
            'term': 360
        })
        assert response.status_code == 400

    def test_term_above_480_returns_400(self, client):
        """Term > 480 months returns 400."""
        response = client.post('/api/calculator/monthly-payment', json={
            'principal': 200000,
            'rate': 0.065,
            'term': 600
        })
        assert response.status_code == 400

    def test_zero_rate_allowed(self, client):
        """Zero rate is allowed (interest-free loan)."""
        response = client.post('/api/calculator/monthly-payment', json={
            'principal': 120000,
            'rate': 0,
            'term': 120
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data['monthly_payment'] == 1000.0  # 120000 / 120

    def test_empty_body_returns_400(self, client):
        """Empty request body returns 400."""
        response = client.post('/api/calculator/monthly-payment')
        assert response.status_code == 400

    def test_response_includes_input(self, client):
        """Response includes input parameters."""
        response = client.post('/api/calculator/monthly-payment', json={
            'principal': 200000,
            'rate': 0.065,
            'term': 360
        })
        data = response.get_json()
        assert 'input' in data
        assert data['input']['principal'] == 200000
        assert data['input']['rate'] == 0.065
        assert data['input']['term'] == 360


class TestRecoupEndpoint:
    """Tests for /api/calculator/recoup endpoint."""

    def test_valid_request_returns_200(self, client):
        """Valid request returns 200."""
        response = client.post('/api/calculator/recoup', json={
            'original_monthly_payment': 1500,
            'refi_monthly_payment': 1200,
            'target_term': 60,
            'refi_cost': 3000
        })
        assert response.status_code == 200
        data = response.get_json()
        assert 'months_to_recoup' in data
        assert 'monthly_savings' in data

    def test_no_savings_returns_valid_response(self, client):
        """When new payment is higher, returns valid response with message."""
        response = client.post('/api/calculator/recoup', json={
            'original_monthly_payment': 1200,
            'refi_monthly_payment': 1500,
            'target_term': 60,
            'refi_cost': 3000
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data['months_to_recoup'] is None
        assert 'message' in data
        assert 'No savings' in data['message']

    def test_missing_field_returns_400(self, client):
        """Missing required field returns 400."""
        response = client.post('/api/calculator/recoup', json={
            'original_monthly_payment': 1500,
            'refi_monthly_payment': 1200,
            'target_term': 60
            # missing refi_cost
        })
        assert response.status_code == 400


class TestAmountRemainingEndpoint:
    """Tests for /api/calculator/amount-remaining endpoint."""

    def test_valid_request_returns_200(self, client):
        """Valid request returns 200."""
        response = client.post('/api/calculator/amount-remaining', json={
            'principal': 200000,
            'monthly_payment': 1264.14,
            'rate': 0.065,
            'months_remaining': 300
        })
        assert response.status_code == 200
        data = response.get_json()
        assert 'amount_remaining' in data

    def test_zero_months_remaining_returns_zero(self, client):
        """Zero months remaining returns 0 balance."""
        response = client.post('/api/calculator/amount-remaining', json={
            'principal': 200000,
            'monthly_payment': 1264.14,
            'rate': 0.065,
            'months_remaining': 0
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data['amount_remaining'] == 0


class TestEfficientFrontierEndpoint:
    """Tests for /api/calculator/efficient-frontier endpoint."""

    def test_valid_request_returns_200(self, client):
        """Valid request returns 200."""
        response = client.post('/api/calculator/efficient-frontier', json={
            'original_principal': 200000,
            'original_rate': 0.065,
            'original_term': 360,
            'current_principal': 180000,
            'term_remaining': 300,
            'new_term': 360,
            'refi_cost': 5000
        })
        assert response.status_code == 200
        data = response.get_json()
        assert 'data' in data
        assert isinstance(data['data'], list)

    def test_current_principal_exceeds_original_returns_422(self, client):
        """Current principal > original returns 422."""
        response = client.post('/api/calculator/efficient-frontier', json={
            'original_principal': 200000,
            'original_rate': 0.065,
            'original_term': 360,
            'current_principal': 250000,  # Exceeds original
            'term_remaining': 300,
            'new_term': 360,
            'refi_cost': 5000
        })
        assert response.status_code == 422

    def test_term_remaining_exceeds_original_returns_422(self, client):
        """Term remaining > original term returns 422."""
        response = client.post('/api/calculator/efficient-frontier', json={
            'original_principal': 200000,
            'original_rate': 0.065,
            'original_term': 360,
            'current_principal': 180000,
            'term_remaining': 400,  # Exceeds original term
            'new_term': 360,
            'refi_cost': 5000
        })
        assert response.status_code == 422


class TestBreakEvenRateEndpoint:
    """Tests for /api/calculator/break-even-rate endpoint."""

    def test_valid_request_returns_200(self, client):
        """Valid request returns 200."""
        response = client.post('/api/calculator/break-even-rate', json={
            'principal': 180000,
            'new_term': 360,
            'target': 100000,
            'current_rate': 0.065
        })
        assert response.status_code == 200
        data = response.get_json()
        assert 'break_even_rate' in data

    def test_missing_field_returns_400(self, client):
        """Missing required field returns 400."""
        response = client.post('/api/calculator/break-even-rate', json={
            'principal': 180000,
            'new_term': 360,
            'target': 100000
            # missing current_rate
        })
        assert response.status_code == 400
