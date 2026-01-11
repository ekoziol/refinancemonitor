import secrets
from . import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import re


class User(UserMixin, db.Model):
    """User account model."""

    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=False)
    email = db.Column(db.String(40), unique=True, nullable=False)
    password = db.Column(
        db.String(200), primary_key=False, unique=False, nullable=False
    )
    credit_score = db.Column(db.Integer, index=False, unique=False, nullable=True)
    created_on = db.Column(db.DateTime, index=False, unique=False, nullable=True)
    updated_on = db.Column(db.DateTime, index=False, unique=False, nullable=True)
    last_login = db.Column(db.DateTime, index=False, unique=False, nullable=True)
    last_paid_date = db.Column(db.DateTime, index=False, unique=False, nullable=True)
    paid = db.Column(db.Integer, index=False, unique=False, nullable=True)
    email_unsubscribed = db.Column(db.Boolean, default=False, nullable=False)
    unsubscribe_token = db.Column(db.String(64), unique=True, nullable=True, index=True)
    mortgages = db.relationship("Mortgage")

    def set_password(self, password):
        """Create hashed password."""
        self.password = generate_password_hash(password, method='sha256')

    def check_password(self, password):
        """Check hashed password."""
        return check_password_hash(self.password, password)

    def generate_unsubscribe_token(self):
        """Generate a unique unsubscribe token for this user."""
        if not self.unsubscribe_token:
            self.unsubscribe_token = secrets.token_urlsafe(32)
        return self.unsubscribe_token

    def __repr__(self):
        return '<User {}>'.format(self.email)


class Mortgage(db.Model):
    __tablename__ = 'mortgage'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    name = db.Column(db.String(100), nullable=False, unique=False)
    zip_code = db.Column(db.String(5), nullable=False, unique=False)
    original_principal = db.Column(db.Float, nullable=False, unique=False)
    original_term = db.Column(db.Integer, nullable=False, unique=False)
    original_interest_rate = db.Column(db.Float, nullable=False, unique=False)
    remaining_principal = db.Column(db.Float, nullable=False, unique=False)
    remaining_term = db.Column(db.Integer, nullable=False, unique=False)
    credit_score = db.Column(db.Integer, nullable=False, unique=False)
    created_on = db.Column(db.DateTime, index=False, unique=False, nullable=True)
    updated_on = db.Column(db.DateTime, index=False, unique=False, nullable=True)
    trackings = db.relationship("Mortgage_Tracking")
    alerts = db.relationship("Alert")


class Mortgage_Tracking(db.Model):
    __tablename__ = 'mortgage_current_value'
    id = db.Column(db.Integer, primary_key=True)
    mortgage_id = db.Column(db.Integer, db.ForeignKey('mortgage.id'))
    current_rate = db.Column(db.Float, nullable=False, unique=False)
    current_remaining_term = db.Column(db.Integer, nullable=False, unique=False)
    current_remaining_principal = db.Column(db.Float, nullable=False, unique=False)

    created_on = db.Column(db.DateTime, index=False, unique=False, nullable=True)
    updated_on = db.Column(db.DateTime, index=False, unique=False, nullable=True)


class Alert(db.Model):
    __tablename__ = 'alert'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    mortgage_id = db.Column(db.Integer, db.ForeignKey('mortgage.id'))
    alert_type = db.Column(db.String, nullable=False, unique=False)
    target_monthly_payment = db.Column(db.Float, nullable=True, unique=False)
    target_interest_rate = db.Column(db.Float, nullable=True, unique=False)
    target_term = db.Column(db.Integer, nullable=False, unique=False)
    estimate_refinance_cost = db.Column(db.Float, nullable=False, unique=False)

    calculated_refinance_cost = db.Column(db.Float, nullable=True, unique=False)

    created_on = db.Column(db.DateTime, index=False, unique=False, nullable=True)
    updated_on = db.Column(db.DateTime, index=False, unique=False, nullable=True)

    initial_payment = db.Column(db.Boolean, index=False, unique=False, nullable=True)
    payment_status = db.Column(db.String, index=False, unique=False, nullable=True)
    initial_period_start = db.Column(
        db.Integer, index=False, unique=False, nullable=True
    )
    initial_period_end = db.Column(db.Integer, index=False, unique=False, nullable=True)
    period_start = db.Column(db.Integer, index=False, unique=False, nullable=True)
    period_end = db.Column(db.Integer, index=False, unique=False, nullable=True)
    price_id = db.Column(db.String, index=False, unique=False, nullable=True)
    stripe_customer_id = db.Column(db.String, index=False, unique=False, nullable=True)
    stripe_invoice_id = db.Column(db.String, index=False, unique=False, nullable=True)
    triggers = db.relationship("Trigger")


class Trigger(db.Model):
    __tablename__ = 'trigger'
    id = db.Column(db.Integer, primary_key=True)
    alert_id = db.Column(db.Integer, db.ForeignKey('alert.id'))
    alert_type = db.Column(db.String, nullable=False, unique=False)
    alert_trigger_status = db.Column(db.Integer, nullable=False, unique=False)
    alert_trigger_reason = db.Column(db.String, nullable=False, unique=False)
    alert_trigger_date = db.Column(
        db.DateTime, index=False, unique=False, nullable=True
    )

    created_on = db.Column(db.DateTime, index=False, unique=False, nullable=True)
    updated_on = db.Column(db.DateTime, index=False, unique=False, nullable=True)


class EmailLog(db.Model):
    """Email delivery tracking and history."""

    __tablename__ = 'email_log'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    email_type = db.Column(
        db.Enum(
            'alert_triggered', 'payment_confirmation', 'welcome',
            'alert_created', 'unsubscribe_confirmation',
            name='email_type_enum'
        ),
        nullable=False,
        index=True
    )
    recipient_email = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    status = db.Column(
        db.Enum(
            'pending', 'sent', 'delivered', 'failed', 'bounced',
            name='email_status_enum'
        ),
        nullable=False,
        default='pending',
        index=True
    )
    alert_id = db.Column(db.Integer, db.ForeignKey('alert.id'), nullable=True)
    trigger_id = db.Column(db.Integer, db.ForeignKey('trigger.id'), nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    sent_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())
    updated_at = db.Column(db.DateTime, onupdate=db.func.now())

    # Relationships
    user = db.relationship('User', backref=db.backref('email_logs', lazy='dynamic'))

    def __repr__(self):
        return '<EmailLog {} to {} - {}>'.format(
            self.email_type, self.recipient_email, self.status
        )


class MortgageRate(db.Model):
    """Mortgage rate data model for tracking daily rates from MortgageNewsDaily."""

    __tablename__ = 'mortgage_rate'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, index=True)
    rate_type = db.Column(
        db.Enum(
            '30_year_fixed', '15_year_fixed', 'FHA_30', 'VA_30',
            '5_1_ARM', '7_1_ARM', '10_1_ARM',
            name='rate_type_enum'
        ),
        nullable=False,
        index=True
    )
    rate = db.Column(db.Numeric(5, 3), nullable=False)  # e.g., 6.875
    points = db.Column(db.Numeric(3, 2), nullable=True)  # e.g., 0.70
    apr = db.Column(db.Numeric(5, 3), nullable=True)
    change_from_previous = db.Column(db.Numeric(4, 3), nullable=True)  # Daily change
    source = db.Column(db.String(100), nullable=False, default='mortgagenewsdaily')

    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())
    updated_at = db.Column(db.DateTime, onupdate=db.func.now())

    __table_args__ = (
        db.UniqueConstraint('date', 'rate_type', name='uq_rate_date_type'),
        db.Index('idx_rate_date_type', 'date', 'rate_type'),
    )

    def __repr__(self):
        return '<MortgageRate {}: {}% on {}>'.format(
            self.rate_type, self.rate, self.date
        )


# Blog models

blog_post_tags = db.Table(
    'blog_post_tags',
    db.Column('post_id', db.Integer, db.ForeignKey('blog_post.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('blog_tag.id'), primary_key=True)
)


class BlogCategory(db.Model):
    """Blog category for organizing posts."""

    __tablename__ = 'blog_category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    slug = db.Column(db.String(120), nullable=False, unique=True, index=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    posts = db.relationship('BlogPost', backref='category', lazy='dynamic')

    def __repr__(self):
        return '<BlogCategory {}>'.format(self.name)

    @staticmethod
    def generate_slug(name):
        slug = name.lower().strip()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[\s_-]+', '-', slug)
        return slug


class BlogTag(db.Model):
    """Blog tag for labeling posts."""

    __tablename__ = 'blog_tag'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    slug = db.Column(db.String(60), nullable=False, unique=True, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return '<BlogTag {}>'.format(self.name)

    @staticmethod
    def generate_slug(name):
        slug = name.lower().strip()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[\s_-]+', '-', slug)
        return slug


class BlogPost(db.Model):
    """Blog post model with SEO fields."""

    __tablename__ = 'blog_post'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(220), nullable=False, unique=True, index=True)
    content = db.Column(db.Text, nullable=False)
    excerpt = db.Column(db.Text, nullable=True)
    featured_image = db.Column(db.String(500), nullable=True)

    # Author (using admin user)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    author = db.relationship('User', backref=db.backref('blog_posts', lazy='dynamic'))

    # Category
    category_id = db.Column(db.Integer, db.ForeignKey('blog_category.id'), nullable=True)

    # Tags (many-to-many)
    tags = db.relationship(
        'BlogTag',
        secondary=blog_post_tags,
        lazy='subquery',
        backref=db.backref('posts', lazy='dynamic')
    )

    # Status
    is_published = db.Column(db.Boolean, default=False, nullable=False, index=True)
    published_at = db.Column(db.DateTime, nullable=True, index=True)

    # SEO fields
    meta_title = db.Column(db.String(70), nullable=True)
    meta_description = db.Column(db.String(160), nullable=True)
    canonical_url = db.Column(db.String(500), nullable=True)

    # Reading time (calculated)
    reading_time = db.Column(db.Integer, nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=True, onupdate=datetime.utcnow)

    def __repr__(self):
        return '<BlogPost {}>'.format(self.title)

    @staticmethod
    def generate_slug(title):
        slug = title.lower().strip()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[\s_-]+', '-', slug)
        return slug

    def calculate_reading_time(self):
        """Calculate reading time based on word count (avg 200 words/min)."""
        if self.content:
            word_count = len(self.content.split())
            self.reading_time = max(1, round(word_count / 200))
        return self.reading_time

    def get_meta_title(self):
        """Return meta title or fallback to post title."""
        return self.meta_title or self.title

    def get_meta_description(self):
        """Return meta description or fallback to excerpt."""
        if self.meta_description:
            return self.meta_description
        if self.excerpt:
            return self.excerpt[:160]
        if self.content:
            return self.content[:160]
        return ''
