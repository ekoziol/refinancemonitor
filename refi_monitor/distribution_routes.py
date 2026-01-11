"""Routes for content distribution endpoints.

Provides:
- RSS feed (/feed.xml)
- Sitemap (/sitemap.xml)
- robots.txt (/robots.txt)
- Newsletter subscription endpoints
"""

from datetime import datetime
from flask import Blueprint, Response, current_app, request, jsonify, url_for
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

from .distribution import rss_generator


distribution_bp = Blueprint('distribution', __name__)


@distribution_bp.route('/feed.xml')
@distribution_bp.route('/rss.xml')
@distribution_bp.route('/blog/feed')
def rss_feed():
    """Generate RSS 2.0 feed for blog content.

    Returns XML feed. Currently returns empty feed until blog
    infrastructure is built.
    """
    # TODO: Fetch posts from database once blog model exists
    # For now, return empty feed structure
    posts = []

    # Example structure that will work once BlogPost model exists:
    # from .models import BlogPost
    # posts = BlogPost.query.filter_by(published=True).order_by(
    #     BlogPost.published_at.desc()
    # ).limit(20).all()
    # posts = [{
    #     'title': p.title,
    #     'slug': p.slug,
    #     'excerpt': p.excerpt,
    #     'content': p.content,
    #     'published_at': p.published_at,
    #     'author': p.author.name if p.author else None,
    #     'categories': [c.name for c in p.categories]
    # } for p in posts]

    xml_content = rss_generator.generate_feed(posts)

    return Response(
        xml_content,
        mimetype='application/rss+xml',
        headers={'Content-Type': 'application/rss+xml; charset=utf-8'}
    )


@distribution_bp.route('/sitemap.xml')
def sitemap():
    """Generate XML sitemap for SEO.

    Includes:
    - Static pages
    - Blog posts (when available)
    - Category pages
    """
    site_url = current_app.config.get('SITE_URL', 'https://refi-alert.com')

    # Create sitemap
    urlset = Element('urlset')
    urlset.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')

    # Static pages
    static_pages = [
        {'loc': '/', 'changefreq': 'daily', 'priority': '1.0'},
        {'loc': '/calculator/', 'changefreq': 'weekly', 'priority': '0.8'},
        {'loc': '/blog/', 'changefreq': 'daily', 'priority': '0.9'},
    ]

    for page in static_pages:
        url_elem = SubElement(urlset, 'url')
        SubElement(url_elem, 'loc').text = f"{site_url}{page['loc']}"
        SubElement(url_elem, 'changefreq').text = page['changefreq']
        SubElement(url_elem, 'priority').text = page['priority']
        SubElement(url_elem, 'lastmod').text = datetime.utcnow().strftime('%Y-%m-%d')

    # TODO: Add blog posts once BlogPost model exists
    # from .models import BlogPost
    # posts = BlogPost.query.filter_by(published=True).all()
    # for post in posts:
    #     url_elem = SubElement(urlset, 'url')
    #     SubElement(url_elem, 'loc').text = f"{site_url}/blog/{post.slug}"
    #     SubElement(url_elem, 'changefreq').text = 'monthly'
    #     SubElement(url_elem, 'priority').text = '0.7'
    #     if post.updated_at:
    #         SubElement(url_elem, 'lastmod').text = post.updated_at.strftime('%Y-%m-%d')

    xml_str = tostring(urlset, encoding='unicode')
    dom = minidom.parseString(xml_str)
    xml_content = dom.toprettyxml(indent='  ')

    return Response(
        xml_content,
        mimetype='application/xml',
        headers={'Content-Type': 'application/xml; charset=utf-8'}
    )


@distribution_bp.route('/robots.txt')
def robots():
    """Generate robots.txt for search engines."""
    site_url = current_app.config.get('SITE_URL', 'https://refi-alert.com')

    content = f"""# robots.txt for {site_url}

User-agent: *
Allow: /
Allow: /blog/
Allow: /calculator/

# Disallow admin and user-specific pages
Disallow: /admin/
Disallow: /dashboard/
Disallow: /manage/
Disallow: /login
Disallow: /signup
Disallow: /checkout/

# Sitemap location
Sitemap: {site_url}/sitemap.xml

# Crawl-delay (be nice to servers)
Crawl-delay: 1
"""

    return Response(
        content,
        mimetype='text/plain',
        headers={'Content-Type': 'text/plain; charset=utf-8'}
    )


@distribution_bp.route('/api/newsletter/subscribe', methods=['POST'])
def newsletter_subscribe():
    """Subscribe email to newsletter.

    Expects JSON: {"email": "user@example.com", "segments": ["us", "rates"]}
    """
    data = request.get_json()

    if not data or not data.get('email'):
        return jsonify({'success': False, 'error': 'Email required'}), 400

    email = data['email'].strip().lower()
    segments = data.get('segments', ['general'])

    # Basic email validation
    if '@' not in email or '.' not in email:
        return jsonify({'success': False, 'error': 'Invalid email format'}), 400

    # TODO: Store subscriber in database once NewsletterSubscriber model exists
    # from .models import NewsletterSubscriber
    # subscriber = NewsletterSubscriber(email=email, segments=segments)
    # db.session.add(subscriber)
    # db.session.commit()

    current_app.logger.info(f"Newsletter subscription: {email}")

    return jsonify({
        'success': True,
        'message': 'Successfully subscribed to newsletter',
        'email': email
    })


@distribution_bp.route('/api/newsletter/unsubscribe', methods=['POST'])
def newsletter_unsubscribe():
    """Unsubscribe email from newsletter."""
    data = request.get_json()

    if not data or not data.get('email'):
        return jsonify({'success': False, 'error': 'Email required'}), 400

    email = data['email'].strip().lower()

    # TODO: Update subscriber status in database
    # from .models import NewsletterSubscriber
    # subscriber = NewsletterSubscriber.query.filter_by(email=email).first()
    # if subscriber:
    #     subscriber.subscribed = False
    #     db.session.commit()

    current_app.logger.info(f"Newsletter unsubscribe: {email}")

    return jsonify({
        'success': True,
        'message': 'Successfully unsubscribed from newsletter'
    })


@distribution_bp.route('/unsubscribe')
def unsubscribe_page():
    """Unsubscribe landing page."""
    # For now, return a simple message
    # TODO: Create proper template once UI is built
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Unsubscribe - RefiAlert</title>
        <style>
            body { font-family: sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }
            .card { background: #f9fafb; border-radius: 8px; padding: 30px; text-align: center; }
            input { padding: 10px; width: 250px; border: 1px solid #ddd; border-radius: 4px; }
            button { padding: 10px 20px; background: #dc2626; color: white; border: none; border-radius: 4px; cursor: pointer; }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>Unsubscribe</h1>
            <p>Enter your email to unsubscribe from our newsletter.</p>
            <form id="unsubscribe-form">
                <input type="email" name="email" placeholder="your@email.com" required>
                <br><br>
                <button type="submit">Unsubscribe</button>
            </form>
            <p id="result"></p>
        </div>
        <script>
            document.getElementById('unsubscribe-form').addEventListener('submit', async (e) => {
                e.preventDefault();
                const email = e.target.email.value;
                const resp = await fetch('/api/newsletter/unsubscribe', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({email})
                });
                const data = await resp.json();
                document.getElementById('result').textContent = data.message || data.error;
            });
        </script>
    </body>
    </html>
    """
