from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

from models import db, User, Post, GalleryImage

api = Blueprint('api', __name__)


@api.route('/creators')
def get_creators():
    """API endpoint to get creators list - Only approved users"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)

    # Base query - only approved users
    query = User.query.filter_by(is_active=True, is_approved=True)

    # Filter by verification
    if request.args.get('verified') == 'true':
        query = query.filter_by(is_verified=True)

    # Filter by featured
    if request.args.get('featured') == 'true':
        query = query.filter_by(is_featured=True)

    # Search
    search = request.args.get('q', '')
    if search:
        query = query.filter(
            db.or_(
                User.username.ilike(f'%{search}%'),
                User.display_name.ilike(f'%{search}%'),
                User.bio.ilike(f'%{search}%')
            )
        )

    # Sort
    sort = request.args.get('sort', 'newest')
    if sort == 'popular':
        query = query.order_by(User.followers_count.desc())
    elif sort == 'oldest':
        query = query.order_by(User.created_at.asc())
    else:  # newest
        query = query.order_by(User.created_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    creators = [user.to_dict() for user in pagination.items]

    return jsonify({
        'creators': creators,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': pagination.page,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev
    })


@api.route('/creator/<username>')
def get_creator(username):
    """API endpoint to get single creator - Only if approved"""
    user = User.query.filter_by(
        username=username, is_active=True, is_approved=True).first_or_404()

    # Get social links
    social_links = [{
        'platform': link.platform,
        'url': link.url,
        'handle': link.handle,
        'is_premium': link.is_premium
    } for link in user.social_links]

    # Get gallery images
    gallery = [{
        'id': img.id,
        'url': img.image_url,
        'caption': img.caption,
        'likes': img.likes,
        'created_at': img.created_at.isoformat()
    } for img in user.gallery_images.filter_by(is_public=True).limit(20).all()]

    data = user.to_dict()
    data['social_links'] = social_links
    data['gallery'] = gallery
    data['email'] = user.email  # Only include if you want to expose

    return jsonify(data)


@api.route('/search')
def search():
    """API endpoint for search"""
    query = request.args.get('q', '')

    if len(query) < 2:
        return jsonify({'creators': [], 'posts': []})

    # Search users
    users = User.query.filter(
        db.and_(
            User.is_active == True,
            db.or_(
                User.username.ilike(f'%{query}%'),
                User.display_name.ilike(f'%{query}%'),
                User.bio.ilike(f'%{query}%')
            )
        )
    ).limit(10).all()

    # Search posts
    posts = Post.query.filter(
        db.and_(
            Post.is_published == True,
            Post.content.ilike(f'%{query}%')
        )
    ).limit(10).all()

    return jsonify({
        'creators': [user.to_dict() for user in users],
        'posts': [{
            'id': post.id,
            'content': post.content[:200],
            'author': post.author.username,
            'created_at': post.created_at.isoformat()
        } for post in posts]
    })


@api.route('/stats')
def stats():
    """API endpoint for platform stats"""
    total_creators = User.query.filter_by(is_active=True).count()
    total_verified = User.query.filter_by(
        is_verified=True, is_active=True).count()
    total_posts = Post.query.filter_by(is_published=True).count()
    total_views = db.session.query(db.func.sum(User.views_count)).scalar() or 0

    # Get trending creators (by followers)
    trending = User.query.filter_by(is_active=True)\
        .order_by(User.followers_count.desc()).limit(5).all()

    return jsonify({
        'total_creators': total_creators,
        'total_verified': total_verified,
        'total_posts': total_posts,
        'total_views': total_views,
        'trending': [user.to_dict() for user in trending]
    })
