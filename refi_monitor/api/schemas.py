"""API request/response schemas using Marshmallow."""
from marshmallow import Schema, fields, validate, validates, ValidationError


class MonthlyPaymentRequestSchema(Schema):
    """Schema for monthly payment calculation request."""
    principal = fields.Float(
        required=True,
        validate=validate.Range(min=0.01, error="Principal must be greater than 0")
    )
    rate = fields.Float(
        required=True,
        validate=validate.Range(min=0, max=0.99, error="Rate must be between 0 and 1")
    )
    term = fields.Integer(
        required=True,
        validate=validate.Range(min=1, max=480, error="Term must be between 1 and 480 months")
    )


class EfficientFrontierRequestSchema(Schema):
    """Schema for efficient frontier calculation request."""
    original_principal = fields.Float(
        required=True,
        validate=validate.Range(min=0.01, error="Original principal must be greater than 0")
    )
    original_rate = fields.Float(
        required=True,
        validate=validate.Range(min=0, max=0.99, error="Rate must be between 0 and 1")
    )
    original_term = fields.Integer(
        required=True,
        validate=validate.Range(min=1, max=480, error="Term must be between 1 and 480 months")
    )
    current_principal = fields.Float(
        required=True,
        validate=validate.Range(min=0.01, error="Current principal must be greater than 0")
    )
    term_remaining = fields.Integer(
        required=True,
        validate=validate.Range(min=1, max=480, error="Term remaining must be between 1 and 480 months")
    )
    new_term = fields.Integer(
        required=True,
        validate=validate.Range(min=1, max=480, error="New term must be between 1 and 480 months")
    )
    refi_cost = fields.Float(
        required=True,
        validate=validate.Range(min=0, error="Refinancing cost cannot be negative")
    )

    @validates('current_principal')
    def validate_current_principal(self, value):
        """Validate current principal doesn't exceed original."""
        # Note: We can't access other fields here easily, validation will be done in endpoint
        pass


class BreakEvenRateRequestSchema(Schema):
    """Schema for break-even rate calculation request."""
    principal = fields.Float(
        required=True,
        validate=validate.Range(min=0.01, error="Principal must be greater than 0")
    )
    new_term = fields.Integer(
        required=True,
        validate=validate.Range(min=1, max=480, error="Term must be between 1 and 480 months")
    )
    target = fields.Float(
        required=True,
        validate=validate.Range(min=0, error="Target cannot be negative")
    )
    current_rate = fields.Float(
        required=True,
        validate=validate.Range(min=0, max=0.99, error="Rate must be between 0 and 1")
    )


class RecoupRequestSchema(Schema):
    """Schema for recoup calculation request."""
    original_monthly_payment = fields.Float(
        required=True,
        validate=validate.Range(min=0.01, error="Original monthly payment must be greater than 0")
    )
    refi_monthly_payment = fields.Float(
        required=True,
        validate=validate.Range(min=0.01, error="Refinanced monthly payment must be greater than 0")
    )
    target_term = fields.Integer(
        required=True,
        validate=validate.Range(min=1, max=480, error="Target term must be between 1 and 480 months")
    )
    refi_cost = fields.Float(
        required=True,
        validate=validate.Range(min=0, error="Refinancing cost cannot be negative")
    )


class AmountRemainingRequestSchema(Schema):
    """Schema for amount remaining calculation request."""
    principal = fields.Float(
        required=True,
        validate=validate.Range(min=0.01, error="Principal must be greater than 0")
    )
    monthly_payment = fields.Float(
        required=True,
        validate=validate.Range(min=0.01, error="Monthly payment must be greater than 0")
    )
    rate = fields.Float(
        required=True,
        validate=validate.Range(min=0.001, max=0.99, error="Rate must be between 0.001 and 1")
    )
    months_remaining = fields.Integer(
        required=True,
        validate=validate.Range(min=0, max=480, error="Months remaining must be between 0 and 480")
    )


# Response schemas for documentation purposes
class MonthlyPaymentResponseSchema(Schema):
    """Schema for monthly payment calculation response."""
    monthly_payment = fields.Float()
    input = fields.Dict()


class ErrorResponseSchema(Schema):
    """Schema for error responses."""
    error = fields.String()
    message = fields.String()
    details = fields.Dict(required=False)
