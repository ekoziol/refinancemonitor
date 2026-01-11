"""Tests for database models."""
import pytest
from datetime import date, datetime
from decimal import Decimal

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from refi_monitor import db, init_app
from refi_monitor.models import (
    User, Mortgage, Mortgage_Tracking, Alert, Trigger, MortgageRate
)


@pytest.fixture
def app():
    """Create application for testing."""
    app = init_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


class TestMortgageRateModel:
    """Tests for MortgageRate model."""

    def test_create_mortgage_rate(self, app):
        """Test creating a MortgageRate record."""
        with app.app_context():
            rate = MortgageRate(
                date=date.today(),
                rate_type='30_year_fixed',
                rate=Decimal('6.875'),
                points=Decimal('0.70'),
                apr=Decimal('7.125'),
                source='mortgagenewsdaily'
            )
            db.session.add(rate)
            db.session.commit()

            # Query and verify
            saved_rate = MortgageRate.query.first()
            assert saved_rate is not None
            assert saved_rate.rate_type == '30_year_fixed'
            assert saved_rate.rate == Decimal('6.875')
            assert saved_rate.points == Decimal('0.70')
            assert saved_rate.source == 'mortgagenewsdaily'

    def test_unique_constraint_date_rate_type(self, app):
        """Test that date + rate_type combination is unique."""
        with app.app_context():
            today = date.today()

            # Create first rate
            rate1 = MortgageRate(
                date=today,
                rate_type='30_year_fixed',
                rate=Decimal('6.875'),
                source='mortgagenewsdaily'
            )
            db.session.add(rate1)
            db.session.commit()

            # Try to create duplicate - should fail
            rate2 = MortgageRate(
                date=today,
                rate_type='30_year_fixed',
                rate=Decimal('6.900'),
                source='mortgagenewsdaily'
            )
            db.session.add(rate2)

            with pytest.raises(Exception):  # IntegrityError
                db.session.commit()

    def test_different_rate_types_same_date(self, app):
        """Test that different rate types on same date are allowed."""
        with app.app_context():
            today = date.today()

            rate_30yr = MortgageRate(
                date=today,
                rate_type='30_year_fixed',
                rate=Decimal('6.875'),
                source='mortgagenewsdaily'
            )
            rate_15yr = MortgageRate(
                date=today,
                rate_type='15_year_fixed',
                rate=Decimal('6.125'),
                source='mortgagenewsdaily'
            )

            db.session.add(rate_30yr)
            db.session.add(rate_15yr)
            db.session.commit()

            rates = MortgageRate.query.filter_by(date=today).all()
            assert len(rates) == 2

    def test_mortgage_rate_repr(self, app):
        """Test MortgageRate string representation."""
        with app.app_context():
            rate = MortgageRate(
                date=date(2026, 1, 11),
                rate_type='30_year_fixed',
                rate=Decimal('6.875'),
                source='mortgagenewsdaily'
            )

            repr_str = repr(rate)
            assert '30_year_fixed' in repr_str
            assert '6.875' in repr_str

    def test_all_rate_types(self, app):
        """Test all valid rate types can be stored."""
        with app.app_context():
            rate_types = [
                '30_year_fixed', '15_year_fixed', 'FHA_30', 'VA_30',
                '5_1_ARM', '7_1_ARM', '10_1_ARM'
            ]

            for i, rate_type in enumerate(rate_types):
                rate = MortgageRate(
                    date=date(2026, 1, i + 1),  # Different dates to avoid unique constraint
                    rate_type=rate_type,
                    rate=Decimal('6.000'),
                    source='mortgagenewsdaily'
                )
                db.session.add(rate)

            db.session.commit()

            assert MortgageRate.query.count() == len(rate_types)

    def test_change_from_previous(self, app):
        """Test change_from_previous field stores correctly."""
        with app.app_context():
            rate = MortgageRate(
                date=date.today(),
                rate_type='30_year_fixed',
                rate=Decimal('6.875'),
                change_from_previous=Decimal('-0.125'),
                source='mortgagenewsdaily'
            )
            db.session.add(rate)
            db.session.commit()

            saved_rate = MortgageRate.query.first()
            assert saved_rate.change_from_previous == Decimal('-0.125')


class TestUserModel:
    """Tests for User model."""

    def test_create_user(self, app):
        """Test creating a User record."""
        with app.app_context():
            user = User(
                name='Test User',
                email='test@example.com',
                password='hashed_password',
                created_on=datetime.utcnow()
            )
            db.session.add(user)
            db.session.commit()

            saved_user = User.query.first()
            assert saved_user.name == 'Test User'
            assert saved_user.email == 'test@example.com'

    def test_user_password_hashing(self, app):
        """Test password hashing and verification."""
        with app.app_context():
            user = User(
                name='Test User',
                email='test@example.com',
                password=''
            )
            user.set_password('mysecretpassword')
            db.session.add(user)
            db.session.commit()

            saved_user = User.query.first()
            assert saved_user.check_password('mysecretpassword')
            assert not saved_user.check_password('wrongpassword')


class TestMortgageModel:
    """Tests for Mortgage model."""

    def test_create_mortgage(self, app):
        """Test creating a Mortgage record."""
        with app.app_context():
            # Create user first
            user = User(
                name='Test User',
                email='test@example.com',
                password='hashed'
            )
            db.session.add(user)
            db.session.commit()

            mortgage = Mortgage(
                user_id=user.id,
                name='Primary Home',
                zip_code='12345',
                original_principal=300000.0,
                original_term=30,
                original_interest_rate=0.0675,
                remaining_principal=275000.0,
                remaining_term=28,
                credit_score=750
            )
            db.session.add(mortgage)
            db.session.commit()

            saved_mortgage = Mortgage.query.first()
            assert saved_mortgage.name == 'Primary Home'
            assert saved_mortgage.original_principal == 300000.0

    def test_mortgage_user_relationship(self, app):
        """Test mortgage belongs to user relationship."""
        with app.app_context():
            user = User(
                name='Test User',
                email='test@example.com',
                password='hashed'
            )
            db.session.add(user)
            db.session.commit()

            mortgage = Mortgage(
                user_id=user.id,
                name='Primary Home',
                zip_code='12345',
                original_principal=300000.0,
                original_term=30,
                original_interest_rate=0.0675,
                remaining_principal=275000.0,
                remaining_term=28,
                credit_score=750
            )
            db.session.add(mortgage)
            db.session.commit()

            # Check relationship
            assert len(user.mortgages) == 1
            assert user.mortgages[0].name == 'Primary Home'


class TestAlertModel:
    """Tests for Alert model."""

    def test_create_alert(self, app):
        """Test creating an Alert record."""
        with app.app_context():
            user = User(
                name='Test User',
                email='test@example.com',
                password='hashed'
            )
            db.session.add(user)
            db.session.commit()

            mortgage = Mortgage(
                user_id=user.id,
                name='Primary Home',
                zip_code='12345',
                original_principal=300000.0,
                original_term=30,
                original_interest_rate=0.0675,
                remaining_principal=275000.0,
                remaining_term=28,
                credit_score=750
            )
            db.session.add(mortgage)
            db.session.commit()

            alert = Alert(
                user_id=user.id,
                mortgage_id=mortgage.id,
                alert_type='Interest Rate',
                target_interest_rate=0.055,
                target_term=30,
                estimate_refinance_cost=3000.0,
                payment_status='active'
            )
            db.session.add(alert)
            db.session.commit()

            saved_alert = Alert.query.first()
            assert saved_alert.alert_type == 'Interest Rate'
            assert saved_alert.target_interest_rate == 0.055


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
