# Content Distribution System

This document describes the automated publishing and distribution system for blog content on RefiAlert.

## Overview

The content distribution system provides:
- **RSS Feed Generation** - Standard RSS 2.0 feed for syndication
- **Email Newsletter** - Weekly digest via SendGrid
- **Social Media Auto-Posting** - Twitter/X and LinkedIn integration
- **Analytics Integration** - GA4 event tracking and Search Console
- **Content Promotion Tracking** - Checklist system for post promotion

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Content Publisher                         │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │  Newsletter │  │ RSS Generator│  │  Social Service   │  │
│  │   Service   │  │              │  │  Twitter/LinkedIn │  │
│  └─────────────┘  └──────────────┘  └───────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Distribution Routes                      │
│  /feed.xml  /sitemap.xml  /robots.txt  /api/newsletter/*    │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. RSS Feed (`/feed.xml`)

Standard RSS 2.0 feed that automatically includes:
- Latest 20 blog posts
- Full content in CDATA encoding
- Author and category metadata
- Atom self-link for aggregators

**Endpoints:**
- `GET /feed.xml`
- `GET /rss.xml`
- `GET /blog/feed`

### 2. Newsletter Service

Weekly email digest using SendGrid API.

**Features:**
- HTML email template with rate summary
- Automatic weekly scheduling (Mondays)
- Subscriber segmentation support
- Open/click rate tracking via SendGrid

**Endpoints:**
- `POST /api/newsletter/subscribe` - Subscribe email
- `POST /api/newsletter/unsubscribe` - Unsubscribe email
- `GET /unsubscribe` - Unsubscribe landing page

**Request format:**
```json
{
  "email": "user@example.com",
  "segments": ["us", "rates"]
}
```

### 3. Social Media Service

Auto-post to Twitter/X and LinkedIn when content is published.

**Twitter/X Features:**
- Auto-truncate text to fit character limit
- URL shortening awareness (23 chars)
- Image upload support
- Tweet ID tracking

**LinkedIn Features:**
- Article sharing with link preview
- Professional formatting
- Public visibility

### 4. SEO Assets

**Sitemap (`/sitemap.xml`):**
- Auto-generated XML sitemap
- Includes static pages and blog posts
- Last modified dates
- Priority hints for crawlers

**robots.txt (`/robots.txt`):**
- Allow/disallow rules
- Sitemap reference
- Crawl-delay setting

### 5. Analytics Integration

**Google Analytics 4:**
- Page view tracking
- Custom events for:
  - Alert creation (`alert_created`)
  - Payments (`purchase`)
  - Content views (`view_item`)
  - Social shares (`share`)
  - Newsletter signups (`sign_up`)

**Google Search Console:**
- Site verification meta tag support
- Configure via `GOOGLE_SITE_VERIFICATION` env var

## Configuration

### Environment Variables

Add to `.env`:

```bash
# Analytics
GA4_MEASUREMENT_ID=G-KN2200EH78
GOOGLE_SITE_VERIFICATION=your-verification-code

# Site Configuration
SITE_URL=https://refi-alert.com
SITE_NAME=RefiAlert
SITE_DESCRIPTION=Monitor mortgage rates...

# Twitter/X API
TWITTER_API_KEY=your-api-key
TWITTER_API_SECRET=your-api-secret
TWITTER_ACCESS_TOKEN=your-access-token
TWITTER_ACCESS_TOKEN_SECRET=your-access-secret

# LinkedIn API
LINKEDIN_CLIENT_ID=your-client-id
LINKEDIN_CLIENT_SECRET=your-client-secret
LINKEDIN_ACCESS_TOKEN=your-access-token

# SendGrid Newsletter
SENDGRID_API_KEY=your-api-key
NEWSLETTER_FROM_EMAIL=newsletter@refi-alert.com
NEWSLETTER_FROM_NAME=RefiAlert Newsletter

# Publishing Schedule
PUBLISH_HOUR=8
PUBLISH_TIMEZONE=America/New_York
```

### API Key Setup

#### Twitter/X Developer Account

1. Apply for developer account at https://developer.twitter.com/
2. Create a project and app
3. Generate API keys and access tokens
4. Enable read/write permissions

#### LinkedIn API

1. Create app at https://developer.linkedin.com/
2. Request `w_member_social` permission
3. Implement OAuth flow to get access token
4. Token expires - need refresh mechanism

#### SendGrid

1. Create account at https://sendgrid.com/
2. Generate API key with mail send permission
3. Verify sender identity

## Usage

### Programmatic Publishing

```python
from refi_monitor.distribution import content_publisher

# Publish a post with auto-distribution
result = content_publisher.publish_post({
    'title': 'Understanding Mortgage Rates in 2026',
    'slug': 'understanding-mortgage-rates-2026',
    'excerpt': 'A comprehensive guide to...',
    'content': '<p>Full HTML content...</p>'
}, auto_distribute=True)

# Get promotion checklist
checklist = content_publisher.get_promotion_checklist(post)
```

### Manual Social Posting

```python
from refi_monitor.distribution import social_service

# Post to Twitter
result = social_service.post_to_twitter(
    text="New blog post: Understanding Mortgage Rates",
    url="https://refi-alert.com/blog/mortgage-rates"
)

# Post to LinkedIn
result = social_service.post_to_linkedin(
    text="Check out our latest analysis...",
    url="https://refi-alert.com/blog/mortgage-rates",
    title="Understanding Mortgage Rates"
)
```

### Sending Newsletter

```python
from refi_monitor.distribution import newsletter_service

# Send weekly digest
result = newsletter_service.send_weekly_digest(
    recipients=['user1@example.com', 'user2@example.com'],
    posts=[
        {'title': 'Post 1', 'excerpt': '...', 'url': '...'},
        {'title': 'Post 2', 'excerpt': '...', 'url': '...'}
    ],
    rate_summary={
        'rate_30': 6.75,
        'rate_15': 5.95,
        'change': 'Down 0.125% from last week'
    }
)
```

## Content Promotion Checklist

Each post generates a promotion checklist:

| Task | Auto | Category |
|------|------|----------|
| Share on Twitter/X | Yes | Social |
| Share on LinkedIn | Yes | Social |
| Include in weekly newsletter | Yes | Email |
| Add to RSS feed | Yes | Syndication |
| Add internal links from related posts | No | SEO |
| Share in relevant communities | No | Outreach |

## Scheduled Jobs

The system adds these jobs to APScheduler:

| Job | Schedule | Description |
|-----|----------|-------------|
| `weekly_newsletter` | Mondays at PUBLISH_HOUR | Send weekly digest |

## Dependencies

Required packages (add to requirements.txt):

```
sendgrid>=6.9.0
tweepy>=4.14.0
requests>=2.28.0
```

## Integration with Blog Infrastructure

**Note:** This distribution system is a framework. Full functionality requires:

1. **BlogPost model** - Database model for blog posts
2. **NewsletterSubscriber model** - For managing subscribers
3. **Blog admin interface** - For creating/scheduling posts

Once the blog infrastructure (ra-n4k) is complete, update:

1. `distribution_routes.py` - Uncomment BlogPost queries
2. `distribution.py` - Wire up scheduled publishing
3. Add newsletter subscriber model and endpoints

## Testing

### Manual Testing

```bash
# Test RSS feed
curl http://localhost:5000/feed.xml

# Test sitemap
curl http://localhost:5000/sitemap.xml

# Test robots.txt
curl http://localhost:5000/robots.txt

# Test newsletter subscribe
curl -X POST http://localhost:5000/api/newsletter/subscribe \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

### Verify Analytics

1. Open browser dev tools
2. Navigate to any page
3. Check Network tab for gtag requests
4. Verify GA4 real-time reports show traffic

## Troubleshooting

### RSS Feed Empty

Expected until blog infrastructure is built. The feed structure is valid but contains no items.

### Social Posts Failing

1. Check API credentials are configured
2. Verify token permissions
3. Check rate limits (Twitter: 300 tweets/3 hours)
4. Review logs for specific error messages

### Newsletter Not Sending

1. Verify `SENDGRID_API_KEY` is set
2. Check sender verification in SendGrid
3. Review SendGrid activity feed for bounces
4. Check application logs for errors

### Analytics Not Tracking

1. Verify `GA4_MEASUREMENT_ID` is correct
2. Check browser ad-blockers
3. Verify analytics.jinja2 is included in templates
4. Check GA4 real-time reports
