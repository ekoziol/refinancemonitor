"""Content distribution service for automated publishing and social sharing.

This module provides:
- Newsletter distribution via SendGrid
- RSS feed generation
- Social media auto-posting (Twitter/X, LinkedIn)
- Scheduled content publishing
- Content promotion tracking
"""

import hashlib
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

from flask import current_app, url_for, render_template_string


class NewsletterService:
    """Email newsletter distribution using SendGrid."""

    def __init__(self, app=None):
        self.app = app
        self._sg_client = None

    def init_app(self, app):
        self.app = app

    @property
    def sg_client(self):
        """Lazy-load SendGrid client."""
        if self._sg_client is None:
            api_key = current_app.config.get('SENDGRID_API_KEY')
            if api_key:
                try:
                    from sendgrid import SendGridAPIClient
                    self._sg_client = SendGridAPIClient(api_key)
                except ImportError:
                    current_app.logger.warning("SendGrid not installed. pip install sendgrid")
        return self._sg_client

    def send_newsletter(
        self,
        recipients: List[str],
        subject: str,
        html_content: str,
        plain_content: Optional[str] = None,
        categories: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Send newsletter to list of recipients.

        Args:
            recipients: List of email addresses
            subject: Email subject line
            html_content: HTML body content
            plain_content: Plain text alternative (auto-generated if not provided)
            categories: SendGrid categories for tracking

        Returns:
            Dict with status and response details
        """
        if not self.sg_client:
            current_app.logger.error("SendGrid client not configured")
            return {'success': False, 'error': 'SendGrid not configured'}

        from_email = current_app.config.get('NEWSLETTER_FROM_EMAIL')
        from_name = current_app.config.get('NEWSLETTER_FROM_NAME')

        try:
            from sendgrid.helpers.mail import Mail, Email, To, Content, Category

            message = Mail(
                from_email=Email(from_email, from_name),
                subject=subject,
            )

            # Add recipients
            for recipient in recipients:
                message.add_to(To(recipient))

            # Add content
            message.add_content(Content("text/html", html_content))
            if plain_content:
                message.add_content(Content("text/plain", plain_content))

            # Add categories for tracking
            if categories:
                for cat in categories:
                    message.add_category(Category(cat))

            response = self.sg_client.send(message)

            current_app.logger.info(
                f"Newsletter sent to {len(recipients)} recipients. "
                f"Status: {response.status_code}"
            )

            return {
                'success': response.status_code in [200, 201, 202],
                'status_code': response.status_code,
                'recipients_count': len(recipients)
            }

        except Exception as e:
            current_app.logger.error(f"Failed to send newsletter: {e}")
            return {'success': False, 'error': str(e)}

    def send_weekly_digest(
        self,
        recipients: List[str],
        posts: List[Dict],
        rate_summary: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Send weekly content digest.

        Args:
            recipients: List of subscriber emails
            posts: List of post dicts with title, excerpt, url
            rate_summary: Optional rate market summary

        Returns:
            Result dict from send_newsletter
        """
        subject = f"RefiAlert Weekly Digest - {datetime.now().strftime('%B %d, %Y')}"

        html_content = render_template_string(
            WEEKLY_DIGEST_TEMPLATE,
            posts=posts,
            rate_summary=rate_summary,
            site_name=current_app.config.get('SITE_NAME'),
            site_url=current_app.config.get('SITE_URL'),
            current_year=datetime.now().year
        )

        return self.send_newsletter(
            recipients=recipients,
            subject=subject,
            html_content=html_content,
            categories=['weekly_digest', 'newsletter']
        )


class RSSFeedGenerator:
    """Generate RSS 2.0 feeds for blog content."""

    def __init__(self, app=None):
        self.app = app

    def init_app(self, app):
        self.app = app

    def generate_feed(
        self,
        posts: List[Dict],
        feed_title: Optional[str] = None,
        feed_description: Optional[str] = None
    ) -> str:
        """Generate RSS 2.0 XML feed.

        Args:
            posts: List of post dicts with:
                - title: Post title
                - slug: URL slug
                - excerpt: Post excerpt/description
                - content: Full HTML content (optional)
                - published_at: Publication datetime
                - author: Author name (optional)
                - categories: List of category names (optional)
            feed_title: Override feed title
            feed_description: Override feed description

        Returns:
            RSS 2.0 XML string
        """
        site_url = current_app.config.get('SITE_URL', '')
        site_name = current_app.config.get('SITE_NAME', 'RefiAlert')
        site_desc = current_app.config.get('SITE_DESCRIPTION', '')

        # Create root RSS element
        rss = Element('rss')
        rss.set('version', '2.0')
        rss.set('xmlns:atom', 'http://www.w3.org/2005/Atom')
        rss.set('xmlns:content', 'http://purl.org/rss/1.0/modules/content/')

        channel = SubElement(rss, 'channel')

        # Channel metadata
        SubElement(channel, 'title').text = feed_title or f"{site_name} Blog"
        SubElement(channel, 'link').text = f"{site_url}/blog/"
        SubElement(channel, 'description').text = feed_description or site_desc
        SubElement(channel, 'language').text = 'en-us'
        SubElement(channel, 'lastBuildDate').text = datetime.utcnow().strftime(
            '%a, %d %b %Y %H:%M:%S +0000'
        )

        # Atom self-link (recommended)
        atom_link = SubElement(channel, 'atom:link')
        atom_link.set('href', f"{site_url}/feed.xml")
        atom_link.set('rel', 'self')
        atom_link.set('type', 'application/rss+xml')

        # Add items
        for post in posts[:20]:  # Limit to 20 items
            item = SubElement(channel, 'item')

            SubElement(item, 'title').text = post.get('title', '')
            SubElement(item, 'link').text = f"{site_url}/blog/{post.get('slug', '')}"
            SubElement(item, 'description').text = post.get('excerpt', '')

            # GUID
            guid = SubElement(item, 'guid')
            guid.text = f"{site_url}/blog/{post.get('slug', '')}"
            guid.set('isPermaLink', 'true')

            # Publication date
            pub_date = post.get('published_at')
            if pub_date:
                if isinstance(pub_date, datetime):
                    SubElement(item, 'pubDate').text = pub_date.strftime(
                        '%a, %d %b %Y %H:%M:%S +0000'
                    )
                else:
                    SubElement(item, 'pubDate').text = str(pub_date)

            # Author
            if post.get('author'):
                SubElement(item, 'author').text = post['author']

            # Categories
            for category in post.get('categories', []):
                SubElement(item, 'category').text = category

            # Full content (encoded)
            if post.get('content'):
                content_encoded = SubElement(item, 'content:encoded')
                content_encoded.text = f"<![CDATA[{post['content']}]]>"

        # Pretty print XML
        xml_str = tostring(rss, encoding='unicode')
        dom = minidom.parseString(xml_str)
        return dom.toprettyxml(indent='  ')


class SocialMediaService:
    """Social media auto-posting service."""

    def __init__(self, app=None):
        self.app = app
        self._twitter_client = None
        self._linkedin_client = None

    def init_app(self, app):
        self.app = app

    def post_to_twitter(
        self,
        text: str,
        url: Optional[str] = None,
        image_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Post content to Twitter/X.

        Args:
            text: Tweet text (will be truncated to fit with URL)
            url: URL to include in tweet
            image_path: Optional path to image file

        Returns:
            Result dict with success status and tweet ID
        """
        api_key = current_app.config.get('TWITTER_API_KEY')
        api_secret = current_app.config.get('TWITTER_API_SECRET')
        access_token = current_app.config.get('TWITTER_ACCESS_TOKEN')
        access_secret = current_app.config.get('TWITTER_ACCESS_TOKEN_SECRET')

        if not all([api_key, api_secret, access_token, access_secret]):
            return {'success': False, 'error': 'Twitter credentials not configured'}

        try:
            import tweepy

            auth = tweepy.OAuthHandler(api_key, api_secret)
            auth.set_access_token(access_token, access_secret)
            api = tweepy.API(auth)

            # Build tweet text
            tweet_text = text
            if url:
                # Twitter shortens URLs to 23 chars
                max_text_len = 280 - 24  # Leave room for URL + space
                if len(tweet_text) > max_text_len:
                    tweet_text = tweet_text[:max_text_len - 3] + '...'
                tweet_text = f"{tweet_text} {url}"

            # Post tweet
            if image_path:
                media = api.media_upload(image_path)
                status = api.update_status(tweet_text, media_ids=[media.media_id])
            else:
                status = api.update_status(tweet_text)

            current_app.logger.info(f"Posted to Twitter: {status.id}")

            return {
                'success': True,
                'tweet_id': str(status.id),
                'url': f"https://twitter.com/i/status/{status.id}"
            }

        except ImportError:
            return {'success': False, 'error': 'tweepy not installed. pip install tweepy'}
        except Exception as e:
            current_app.logger.error(f"Twitter post failed: {e}")
            return {'success': False, 'error': str(e)}

    def post_to_linkedin(
        self,
        text: str,
        url: Optional[str] = None,
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """Post content to LinkedIn.

        Args:
            text: Post text
            url: URL to share (creates link preview)
            title: Title for link preview

        Returns:
            Result dict with success status
        """
        access_token = current_app.config.get('LINKEDIN_ACCESS_TOKEN')

        if not access_token:
            return {'success': False, 'error': 'LinkedIn access token not configured'}

        try:
            import requests

            # Get user URN (required for posting)
            profile_url = "https://api.linkedin.com/v2/me"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0"
            }

            profile_resp = requests.get(profile_url, headers=headers)
            if profile_resp.status_code != 200:
                return {'success': False, 'error': 'Failed to get LinkedIn profile'}

            profile_data = profile_resp.json()
            author_urn = f"urn:li:person:{profile_data['id']}"

            # Create share
            share_url = "https://api.linkedin.com/v2/ugcPosts"

            share_content = {
                "author": author_urn,
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {"text": text},
                        "shareMediaCategory": "ARTICLE" if url else "NONE"
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                }
            }

            if url:
                share_content["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [{
                    "status": "READY",
                    "originalUrl": url,
                    "title": {"text": title or ""},
                }]

            share_resp = requests.post(share_url, headers=headers, json=share_content)

            if share_resp.status_code in [200, 201]:
                current_app.logger.info("Posted to LinkedIn successfully")
                return {'success': True, 'response': share_resp.json()}
            else:
                return {
                    'success': False,
                    'error': f"LinkedIn API error: {share_resp.status_code}"
                }

        except ImportError:
            return {'success': False, 'error': 'requests not installed'}
        except Exception as e:
            current_app.logger.error(f"LinkedIn post failed: {e}")
            return {'success': False, 'error': str(e)}

    def distribute_post(
        self,
        title: str,
        excerpt: str,
        url: str,
        platforms: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Distribute a blog post to multiple social platforms.

        Args:
            title: Post title
            excerpt: Short excerpt for social posts
            url: Full URL to the post
            platforms: List of platforms ['twitter', 'linkedin'] or None for all

        Returns:
            Dict with results for each platform
        """
        platforms = platforms or ['twitter', 'linkedin']
        results = {}

        if 'twitter' in platforms:
            twitter_text = f"{title}\n\n{excerpt[:180]}..."
            results['twitter'] = self.post_to_twitter(twitter_text, url)

        if 'linkedin' in platforms:
            linkedin_text = f"{title}\n\n{excerpt}\n\nRead more on RefiAlert"
            results['linkedin'] = self.post_to_linkedin(linkedin_text, url, title)

        return results


class ContentPublisher:
    """Scheduled content publishing service."""

    def __init__(self, app=None):
        self.app = app
        self.newsletter = NewsletterService()
        self.rss = RSSFeedGenerator()
        self.social = SocialMediaService()

    def init_app(self, app):
        self.app = app
        self.newsletter.init_app(app)
        self.rss.init_app(app)
        self.social.init_app(app)

    def publish_post(self, post: Dict, auto_distribute: bool = True) -> Dict[str, Any]:
        """Publish a blog post and optionally distribute to social channels.

        Args:
            post: Post dict with title, slug, excerpt, content, etc.
            auto_distribute: Whether to auto-post to social media

        Returns:
            Result dict with publication and distribution status
        """
        results = {
            'published': True,
            'published_at': datetime.utcnow(),
            'distributions': {}
        }

        site_url = current_app.config.get('SITE_URL', '')
        post_url = f"{site_url}/blog/{post.get('slug', '')}"

        if auto_distribute:
            results['distributions'] = self.social.distribute_post(
                title=post.get('title', ''),
                excerpt=post.get('excerpt', ''),
                url=post_url,
                platforms=['twitter', 'linkedin']
            )

        current_app.logger.info(f"Published post: {post.get('title')}")

        return results

    def get_promotion_checklist(self, post: Dict) -> List[Dict]:
        """Generate content promotion checklist for a post.

        Args:
            post: Post dict

        Returns:
            List of checklist items with status
        """
        post_id = post.get('id') or hashlib.md5(
            post.get('slug', '').encode()
        ).hexdigest()[:8]

        checklist = [
            {
                'id': f'{post_id}_twitter',
                'task': 'Share on Twitter/X',
                'category': 'social',
                'completed': False,
                'auto': True
            },
            {
                'id': f'{post_id}_linkedin',
                'task': 'Share on LinkedIn',
                'category': 'social',
                'completed': False,
                'auto': True
            },
            {
                'id': f'{post_id}_newsletter',
                'task': 'Include in weekly newsletter',
                'category': 'email',
                'completed': False,
                'auto': True
            },
            {
                'id': f'{post_id}_rss',
                'task': 'Add to RSS feed',
                'category': 'syndication',
                'completed': True,  # Auto-included
                'auto': True
            },
            {
                'id': f'{post_id}_internal_links',
                'task': 'Add internal links from related posts',
                'category': 'seo',
                'completed': False,
                'auto': False
            },
            {
                'id': f'{post_id}_communities',
                'task': 'Share in relevant communities (manual)',
                'category': 'outreach',
                'completed': False,
                'auto': False
            }
        ]

        return checklist


# Email template for weekly digest
WEEKLY_DIGEST_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ site_name }} Weekly Digest</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #2563eb; color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }
        .content { background: #f9fafb; padding: 30px; }
        .post { background: white; padding: 20px; margin-bottom: 15px; border-radius: 8px; border: 1px solid #e5e7eb; }
        .post h3 { margin: 0 0 10px 0; color: #1f2937; }
        .post p { margin: 0 0 10px 0; color: #6b7280; }
        .post a { color: #2563eb; text-decoration: none; font-weight: 500; }
        .rate-box { background: #dbeafe; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .footer { text-align: center; padding: 20px; color: #9ca3af; font-size: 12px; }
        .btn { display: inline-block; background: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ site_name }} Weekly Digest</h1>
        <p>Your weekly mortgage rate insights</p>
    </div>
    <div class="content">
        {% if rate_summary %}
        <div class="rate-box">
            <h2>This Week's Rates</h2>
            <p><strong>30-Year Fixed:</strong> {{ rate_summary.rate_30 }}%</p>
            <p><strong>15-Year Fixed:</strong> {{ rate_summary.rate_15 }}%</p>
            {% if rate_summary.change %}
            <p><em>{{ rate_summary.change }}</em></p>
            {% endif %}
        </div>
        {% endif %}

        <h2>Latest Articles</h2>
        {% for post in posts %}
        <div class="post">
            <h3>{{ post.title }}</h3>
            <p>{{ post.excerpt }}</p>
            <a href="{{ post.url }}">Read more →</a>
        </div>
        {% endfor %}

        <p style="text-align: center; margin-top: 30px;">
            <a href="{{ site_url }}/dashboard" class="btn">Check Your Alerts</a>
        </p>
    </div>
    <div class="footer">
        <p>© {{ current_year }} {{ site_name }}. All rights reserved.</p>
        <p>
            <a href="{{ site_url }}/unsubscribe">Unsubscribe</a> |
            <a href="{{ site_url }}/preferences">Email Preferences</a>
        </p>
    </div>
</body>
</html>
"""


# Initialize services as singletons
newsletter_service = NewsletterService()
rss_generator = RSSFeedGenerator()
social_service = SocialMediaService()
content_publisher = ContentPublisher()


def init_distribution(app):
    """Initialize distribution services with Flask app."""
    newsletter_service.init_app(app)
    rss_generator.init_app(app)
    social_service.init_app(app)
    content_publisher.init_app(app)


def schedule_distribution_jobs(scheduler):
    """Add distribution jobs to APScheduler.

    Args:
        scheduler: APScheduler instance
    """
    from apscheduler.triggers.cron import CronTrigger
    from flask import current_app

    publish_hour = current_app.config.get('PUBLISH_HOUR', 8)

    # Weekly newsletter - Mondays at configured hour
    scheduler.add_job(
        func=send_scheduled_newsletter,
        trigger=CronTrigger(day_of_week='mon', hour=publish_hour),
        id='weekly_newsletter',
        name='Send weekly newsletter digest',
        replace_existing=True
    )

    current_app.logger.info(
        f"Distribution jobs scheduled (newsletter: Mondays at {publish_hour}:00)"
    )


def send_scheduled_newsletter():
    """Send the weekly newsletter digest.

    This function is called by the scheduler.
    """
    from flask import current_app

    # TODO: Fetch subscribers from database
    # TODO: Fetch recent posts from database
    # For now, this is a placeholder that will work once blog infrastructure exists

    current_app.logger.info("Weekly newsletter job triggered (awaiting blog infrastructure)")
