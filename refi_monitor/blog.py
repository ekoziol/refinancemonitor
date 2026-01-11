"""Blog routes for the Refinance Monitor blog."""
from flask import Blueprint, render_template, abort, request, redirect, url_for, flash, Response, make_response
from flask_login import login_required, current_user
from datetime import datetime
from . import db
from .models import BlogPost, BlogCategory, BlogTag

# Blueprint Configuration
blog_bp = Blueprint(
    'blog_bp', __name__, template_folder='templates', static_folder='static'
)

# Number of posts per page
POSTS_PER_PAGE = 10


@blog_bp.route('/blog')
def blog_index():
    """Blog listing page with pagination."""
    page = request.args.get('page', 1, type=int)
    posts = BlogPost.query.filter_by(is_published=True)\
        .order_by(BlogPost.published_at.desc())\
        .paginate(page=page, per_page=POSTS_PER_PAGE, error_out=False)

    categories = BlogCategory.query.all()
    recent_posts = BlogPost.query.filter_by(is_published=True)\
        .order_by(BlogPost.published_at.desc())\
        .limit(5).all()

    return render_template(
        'blog/index.jinja2',
        title='Blog',
        description='Refinancing tips, mortgage market updates, and financial advice',
        posts=posts,
        categories=categories,
        recent_posts=recent_posts,
    )


@blog_bp.route('/blog/<slug>')
def blog_post(slug):
    """Single blog post page."""
    post = BlogPost.query.filter_by(slug=slug, is_published=True).first_or_404()

    categories = BlogCategory.query.all()
    recent_posts = BlogPost.query.filter_by(is_published=True)\
        .filter(BlogPost.id != post.id)\
        .order_by(BlogPost.published_at.desc())\
        .limit(5).all()

    # Get related posts (same category)
    related_posts = []
    if post.category:
        related_posts = BlogPost.query.filter_by(
            is_published=True,
            category_id=post.category_id
        ).filter(BlogPost.id != post.id)\
         .order_by(BlogPost.published_at.desc())\
         .limit(3).all()

    return render_template(
        'blog/post.jinja2',
        title=post.get_meta_title(),
        description=post.get_meta_description(),
        post=post,
        categories=categories,
        recent_posts=recent_posts,
        related_posts=related_posts,
    )


@blog_bp.route('/blog/category/<slug>')
def blog_category(slug):
    """Blog posts by category."""
    category = BlogCategory.query.filter_by(slug=slug).first_or_404()
    page = request.args.get('page', 1, type=int)

    posts = BlogPost.query.filter_by(is_published=True, category_id=category.id)\
        .order_by(BlogPost.published_at.desc())\
        .paginate(page=page, per_page=POSTS_PER_PAGE, error_out=False)

    categories = BlogCategory.query.all()
    recent_posts = BlogPost.query.filter_by(is_published=True)\
        .order_by(BlogPost.published_at.desc())\
        .limit(5).all()

    return render_template(
        'blog/category.jinja2',
        title=f'{category.name} - Blog',
        description=category.description or f'Posts about {category.name}',
        category=category,
        posts=posts,
        categories=categories,
        recent_posts=recent_posts,
    )


@blog_bp.route('/blog/tag/<slug>')
def blog_tag(slug):
    """Blog posts by tag."""
    tag = BlogTag.query.filter_by(slug=slug).first_or_404()
    page = request.args.get('page', 1, type=int)

    posts = tag.posts.filter_by(is_published=True)\
        .order_by(BlogPost.published_at.desc())\
        .paginate(page=page, per_page=POSTS_PER_PAGE, error_out=False)

    categories = BlogCategory.query.all()
    recent_posts = BlogPost.query.filter_by(is_published=True)\
        .order_by(BlogPost.published_at.desc())\
        .limit(5).all()

    return render_template(
        'blog/tag.jinja2',
        title=f'{tag.name} - Blog',
        description=f'Posts tagged with {tag.name}',
        tag=tag,
        posts=posts,
        categories=categories,
        recent_posts=recent_posts,
    )


# SEO Routes

@blog_bp.route('/sitemap.xml')
def sitemap():
    """Generate XML sitemap for blog posts."""
    pages = []

    # Add blog index
    pages.append({
        'loc': url_for('blog_bp.blog_index', _external=True),
        'changefreq': 'daily',
        'priority': '0.9'
    })

    # Add all published posts
    posts = BlogPost.query.filter_by(is_published=True).all()
    for post in posts:
        pages.append({
            'loc': url_for('blog_bp.blog_post', slug=post.slug, _external=True),
            'lastmod': (post.updated_at or post.published_at).strftime('%Y-%m-%d') if (post.updated_at or post.published_at) else '',
            'changefreq': 'monthly',
            'priority': '0.8'
        })

    # Add categories
    categories = BlogCategory.query.all()
    for category in categories:
        pages.append({
            'loc': url_for('blog_bp.blog_category', slug=category.slug, _external=True),
            'changefreq': 'weekly',
            'priority': '0.6'
        })

    # Add tags
    tags = BlogTag.query.all()
    for tag in tags:
        pages.append({
            'loc': url_for('blog_bp.blog_tag', slug=tag.slug, _external=True),
            'changefreq': 'weekly',
            'priority': '0.5'
        })

    sitemap_xml = render_template('blog/sitemap.xml', pages=pages)
    response = make_response(sitemap_xml)
    response.headers['Content-Type'] = 'application/xml'
    return response


@blog_bp.route('/robots.txt')
def robots():
    """Generate robots.txt."""
    robots_txt = f"""User-agent: *
Allow: /blog/
Disallow: /admin/

Sitemap: {url_for('blog_bp.sitemap', _external=True)}
"""
    response = make_response(robots_txt)
    response.headers['Content-Type'] = 'text/plain'
    return response


# Admin routes for blog management

@blog_bp.route('/admin/blog')
@login_required
def admin_blog_list():
    """Admin blog post list."""
    page = request.args.get('page', 1, type=int)
    posts = BlogPost.query.order_by(BlogPost.created_at.desc())\
        .paginate(page=page, per_page=20, error_out=False)

    return render_template(
        'blog/admin/list.jinja2',
        title='Manage Blog Posts',
        posts=posts,
    )


@blog_bp.route('/admin/blog/create', methods=['GET', 'POST'])
@login_required
def admin_blog_create():
    """Create a new blog post."""
    categories = BlogCategory.query.all()
    tags = BlogTag.query.all()

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        excerpt = request.form.get('excerpt', '').strip()
        featured_image = request.form.get('featured_image', '').strip()
        category_id = request.form.get('category_id', type=int)
        tag_ids = request.form.getlist('tags', type=int)
        meta_title = request.form.get('meta_title', '').strip()
        meta_description = request.form.get('meta_description', '').strip()
        is_published = request.form.get('is_published') == 'on'

        if not title or not content:
            flash('Title and content are required.', 'error')
            return render_template(
                'blog/admin/edit.jinja2',
                title='Create Blog Post',
                post=None,
                categories=categories,
                tags=tags,
            )

        # Generate slug
        slug = BlogPost.generate_slug(title)

        # Check if slug already exists
        existing = BlogPost.query.filter_by(slug=slug).first()
        if existing:
            slug = f"{slug}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        post = BlogPost(
            title=title,
            slug=slug,
            content=content,
            excerpt=excerpt or None,
            featured_image=featured_image or None,
            author_id=current_user.id,
            category_id=category_id if category_id else None,
            meta_title=meta_title or None,
            meta_description=meta_description or None,
            is_published=is_published,
            published_at=datetime.utcnow() if is_published else None,
        )

        # Calculate reading time
        post.calculate_reading_time()

        # Add tags
        for tag_id in tag_ids:
            tag = BlogTag.query.get(tag_id)
            if tag:
                post.tags.append(tag)

        db.session.add(post)
        db.session.commit()

        flash('Blog post created successfully!', 'success')
        return redirect(url_for('blog_bp.admin_blog_list'))

    return render_template(
        'blog/admin/edit.jinja2',
        title='Create Blog Post',
        post=None,
        categories=categories,
        tags=tags,
    )


@blog_bp.route('/admin/blog/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_blog_edit(post_id):
    """Edit an existing blog post."""
    post = BlogPost.query.get_or_404(post_id)
    categories = BlogCategory.query.all()
    tags = BlogTag.query.all()

    if request.method == 'POST':
        post.title = request.form.get('title', '').strip()
        post.content = request.form.get('content', '').strip()
        post.excerpt = request.form.get('excerpt', '').strip() or None
        post.featured_image = request.form.get('featured_image', '').strip() or None
        post.category_id = request.form.get('category_id', type=int) or None
        post.meta_title = request.form.get('meta_title', '').strip() or None
        post.meta_description = request.form.get('meta_description', '').strip() or None

        was_published = post.is_published
        is_published = request.form.get('is_published') == 'on'
        post.is_published = is_published

        # Set published_at if newly published
        if is_published and not was_published:
            post.published_at = datetime.utcnow()

        # Update slug if title changed significantly
        new_slug = BlogPost.generate_slug(post.title)
        if new_slug != post.slug:
            existing = BlogPost.query.filter_by(slug=new_slug).filter(BlogPost.id != post.id).first()
            if not existing:
                post.slug = new_slug

        # Calculate reading time
        post.calculate_reading_time()

        # Update tags
        tag_ids = request.form.getlist('tags', type=int)
        post.tags = []
        for tag_id in tag_ids:
            tag = BlogTag.query.get(tag_id)
            if tag:
                post.tags.append(tag)

        db.session.commit()

        flash('Blog post updated successfully!', 'success')
        return redirect(url_for('blog_bp.admin_blog_list'))

    return render_template(
        'blog/admin/edit.jinja2',
        title='Edit Blog Post',
        post=post,
        categories=categories,
        tags=tags,
    )


@blog_bp.route('/admin/blog/<int:post_id>/delete', methods=['POST'])
@login_required
def admin_blog_delete(post_id):
    """Delete a blog post."""
    post = BlogPost.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()

    flash('Blog post deleted.', 'success')
    return redirect(url_for('blog_bp.admin_blog_list'))


# Category management

@blog_bp.route('/admin/blog/categories')
@login_required
def admin_category_list():
    """Admin category list."""
    categories = BlogCategory.query.order_by(BlogCategory.name).all()
    return render_template(
        'blog/admin/categories.jinja2',
        title='Manage Categories',
        categories=categories,
    )


@blog_bp.route('/admin/blog/categories/create', methods=['POST'])
@login_required
def admin_category_create():
    """Create a new category."""
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()

    if not name:
        flash('Category name is required.', 'error')
        return redirect(url_for('blog_bp.admin_category_list'))

    slug = BlogCategory.generate_slug(name)
    existing = BlogCategory.query.filter_by(slug=slug).first()
    if existing:
        flash('A category with this name already exists.', 'error')
        return redirect(url_for('blog_bp.admin_category_list'))

    category = BlogCategory(name=name, slug=slug, description=description or None)
    db.session.add(category)
    db.session.commit()

    flash('Category created successfully!', 'success')
    return redirect(url_for('blog_bp.admin_category_list'))


@blog_bp.route('/admin/blog/categories/<int:category_id>/delete', methods=['POST'])
@login_required
def admin_category_delete(category_id):
    """Delete a category."""
    category = BlogCategory.query.get_or_404(category_id)
    db.session.delete(category)
    db.session.commit()

    flash('Category deleted.', 'success')
    return redirect(url_for('blog_bp.admin_category_list'))


# Tag management

@blog_bp.route('/admin/blog/tags')
@login_required
def admin_tag_list():
    """Admin tag list."""
    tags = BlogTag.query.order_by(BlogTag.name).all()
    return render_template(
        'blog/admin/tags.jinja2',
        title='Manage Tags',
        tags=tags,
    )


@blog_bp.route('/admin/blog/tags/create', methods=['POST'])
@login_required
def admin_tag_create():
    """Create a new tag."""
    name = request.form.get('name', '').strip()

    if not name:
        flash('Tag name is required.', 'error')
        return redirect(url_for('blog_bp.admin_tag_list'))

    slug = BlogTag.generate_slug(name)
    existing = BlogTag.query.filter_by(slug=slug).first()
    if existing:
        flash('A tag with this name already exists.', 'error')
        return redirect(url_for('blog_bp.admin_tag_list'))

    tag = BlogTag(name=name, slug=slug)
    db.session.add(tag)
    db.session.commit()

    flash('Tag created successfully!', 'success')
    return redirect(url_for('blog_bp.admin_tag_list'))


@blog_bp.route('/admin/blog/tags/<int:tag_id>/delete', methods=['POST'])
@login_required
def admin_tag_delete(tag_id):
    """Delete a tag."""
    tag = BlogTag.query.get_or_404(tag_id)
    db.session.delete(tag)
    db.session.commit()

    flash('Tag deleted.', 'success')
    return redirect(url_for('blog_bp.admin_tag_list'))
