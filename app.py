import random  # Add this at the top of your app.py with other imports
import os
import secrets
from datetime import datetime, timedelta
from PIL import Image
from flask import Flask, render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix

from config import config
from models import db, User, SocialLink, GalleryImage, Post, Comment, Follow, VerificationRequest, Notification
from forms import (
    LoginForm, RegistrationForm, ProfileForm, SocialLinkForm,
    AvatarUploadForm, WallpaperUploadForm, GalleryImageForm,
    PostForm, SearchForm, ContactForm, VerificationRequestForm
)

# Initialize extensions
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Login manager settings
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Create upload directories
    os.makedirs(os.path.join(
        app.config['UPLOAD_FOLDER'], 'avatars'), exist_ok=True)
    os.makedirs(os.path.join(
        app.config['UPLOAD_FOLDER'], 'wallpapers'), exist_ok=True)
    os.makedirs(os.path.join(
        app.config['UPLOAD_FOLDER'], 'gallery'), exist_ok=True)
    os.makedirs(os.path.join(
        app.config['UPLOAD_FOLDER'], 'gallery', 'thumbnails'), exist_ok=True)
    os.makedirs(os.path.join(
        app.config['UPLOAD_FOLDER'], 'verification'), exist_ok=True)
    os.makedirs(os.path.join(
        app.config['UPLOAD_FOLDER'], 'posts'), exist_ok=True)

    # Create database tables
    with app.app_context():
        db.create_all()
        print("✅ Database tables verified/created")

        # Create admin user if not exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@velvetsignals.com',
                display_name='Administrator',
                is_admin=True,
                is_verified=True,
                is_active=True,
                is_approved=True
            )
            admin.password = 'Admin123!'
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin user created - Username: admin, Password: Admin123!")

    # Context processor to make csrf_token available in all templates
    @app.context_processor
    def inject_csrf_token():
        from flask_wtf.csrf import generate_csrf
        return dict(csrf_token=generate_csrf)

    # Register template filters
    @app.template_filter('time_ago')
    def time_ago_filter(dt):
        """Convert datetime to 'time ago' string"""
        if not dt:
            return 'just now'

        now = datetime.utcnow()
        diff = now - dt

        seconds = diff.total_seconds()
        if seconds < 60:
            return 'just now'
        minutes = seconds / 60
        if minutes < 60:
            return f'{int(minutes)} minute{"s" if minutes >= 2 else ""} ago'
        hours = minutes / 60
        if hours < 24:
            return f'{int(hours)} hour{"s" if hours >= 2 else ""} ago'
        days = hours / 24
        if days < 30:
            return f'{int(days)} day{"s" if days >= 2 else ""} ago'
        months = days / 30
        if months < 12:
            return f'{int(months)} month{"s" if months >= 2 else ""} ago'
        years = months / 12
        return f'{int(years)} year{"s" if years >= 2 else ""} ago'

    # ===== REGISTER ALL BLUEPRINTS HERE (ONCE!) =====
    from auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    from admin import admin as admin_blueprint
    app.register_blueprint(admin_blueprint, url_prefix='/admin')

    from api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api')

    from profile_routes import profile_bp
    app.register_blueprint(profile_bp)  # <-- ONLY REGISTER HERE, ONCE

    # ===== MAIN ROUTES =====
    @app.route('/')
    def index():
        """Homepage - Only show approved creators, shuffled"""
        # Get ALL featured creators (only approved ones)
        all_featured = User.query.filter_by(
            is_featured=True, is_active=True, is_approved=True).all()

        # Shuffle and take first 6
        random.shuffle(all_featured)
        featured_creators = all_featured[:6]

        # Get ALL approved creators
        all_recent = User.query.filter_by(
            is_active=True, is_approved=True).all()

        # Shuffle and take first 12
        random.shuffle(all_recent)
        recent_creators = all_recent[:12]

        # Get trending posts (keep as is - by likes)
        trending_posts = Post.query.filter_by(is_published=True)\
            .order_by(Post.likes.desc()).limit(5).all()

        # Stats for homepage
        total_creators = User.query.filter_by(
            is_active=True, is_approved=True).count()
        total_views = db.session.query(
            db.func.sum(User.views_count)).scalar() or 0
        total_posts = Post.query.count()

        return render_template('index.html',
                               featured_creators=featured_creators,
                               recent_creators=recent_creators,
                               trending_posts=trending_posts,
                               total_creators=total_creators,
                               total_views=total_views,
                               total_posts=total_posts)

    # Register error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403

    # Register context processors
    @app.context_processor
    def utility_processor():
        def pluralize(count, singular, plural=None):
            if not plural:
                plural = singular + 's'
            return singular if count == 1 else plural
        return dict(pluralize=pluralize)

    @app.route('/creators')
    def creators():
        """Browse all creators - Only show approved ones, shuffled"""
        page = request.args.get('page', 1, type=int)
        per_page = app.config.get('CREATORS_PER_PAGE', 12)

        # Filter by verification status
        filter_type = request.args.get('filter', 'all')
        search_query = request.args.get('q', '')
        # Keep for template compatibility
        sort_by = request.args.get('sort', 'newest')

        # Base query - only approved and active users
        query = User.query.filter_by(is_active=True, is_approved=True)

        if filter_type == 'verified':
            query = query.filter_by(is_verified=True)
        elif filter_type == 'featured':
            query = query.filter_by(is_featured=True)

        # Search functionality
        if search_query:
            query = query.filter(
                db.or_(
                    User.username.ilike(f'%{search_query}%'),
                    User.display_name.ilike(f'%{search_query}%'),
                    User.bio.ilike(f'%{search_query}%')
                )
            )

        # Get all creators matching the query
        all_creators = list(query.all())

        # Shuffle the list randomly
        random.shuffle(all_creators)

        # Calculate pagination
        total = len(all_creators)
        start = (page - 1) * per_page
        end = min(start + per_page, total)

        # Get the items for current page
        if total > 0:
            creators_page = all_creators[start:end]
        else:
            creators_page = []

        # Create pagination object
        class Pagination:
            def __init__(self, items, page, per_page, total):
                self.items = items
                self.page = page
                self.per_page = per_page
                self.total = total
                self.pages = (total + per_page -
                              1) // per_page if total > 0 else 1
                self.has_prev = page > 1
                self.has_next = page < self.pages
                self.prev_num = page - 1 if self.has_prev else None
                self.next_num = page + 1 if self.has_next else None
                self.first = start + 1 if total > 0 else 0
                self.last = end if total > 0 else 0

            def iter_pages(self, left_edge=2, left_current=2, right_current=5, right_edge=2):
                """Generate page numbers for pagination"""
                # This is a simplified version that works with Flask's pagination template
                pages = []
                for num in range(1, self.pages + 1):
                    if num <= left_edge or \
                        (self.page - left_current - 1 < num < self.page + right_current) or \
                            num > self.pages - right_edge:
                        if pages and num - pages[-1] > 1:
                            yield None
                        yield num
                        pages.append(num)

        pagination = Pagination(creators_page, page, per_page, total)

        return render_template('creators.html',
                               creators=creators_page,
                               pagination=pagination,
                               filter_type=filter_type,
                               search_query=search_query,
                               sort_by=sort_by)

    @app.route('/creator/<username>')
    def creator_profile(username):
        """View a creator's public profile - Only if approved"""
        user = User.query.filter_by(
            username=username, is_active=True, is_approved=True).first_or_404()

        # Increment view count
        user.views_count += 1
        db.session.commit()

        # Get user's posts
        posts = Post.query.filter_by(user_id=user.id, is_published=True)\
            .order_by(Post.created_at.desc()).limit(10).all()

        # Get gallery images
        gallery_items = GalleryImage.query.filter_by(user_id=user.id, is_public=True)\
            .order_by(GalleryImage.created_at.desc()).limit(12).all()

        # Normalize gallery items for template
        gallery = []
        for item in gallery_items:
            gallery.append({
                'id': item.id,
                'url': getattr(item, 'media_url', None) or getattr(item, 'image_url', ''),
                'thumbnail_url': getattr(item, 'thumbnail_url', None),
                'caption': item.caption,
                'media_type': getattr(item, 'media_type', 'image'),
                'likes': item.likes,
                'created_at': item.created_at
            })

        # Get social links
        social_links = SocialLink.query.filter_by(user_id=user.id).all()

        # Check if current user is following this creator
        is_following = False
        if current_user.is_authenticated:
            is_following = Follow.query.filter_by(
                follower_id=current_user.id,
                followed_id=user.id
            ).first() is not None

        return render_template('profile.html',
                               profile_user=user,
                               posts=posts,
                               gallery=gallery,
                               social_links=social_links,
                               is_following=is_following)

    @app.route('/dashboard')
    @login_required
    def dashboard():
        """User dashboard"""
        # Get user's recent activity
        recent_posts = Post.query.filter_by(user_id=current_user.id)\
            .order_by(Post.created_at.desc()).limit(5).all()

        # Get recent notifications
        notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False)\
            .order_by(Notification.created_at.desc()).limit(10).all()

        # Get gallery media (both images and videos)
        gallery_media = GalleryImage.query.filter_by(user_id=current_user.id)\
            .order_by(GalleryImage.created_at.desc()).all()

        # Stats
        total_followers = Follow.query.filter_by(
            followed_id=current_user.id).count()
        total_following = Follow.query.filter_by(
            follower_id=current_user.id).count()
        total_posts = Post.query.filter_by(user_id=current_user.id).count()
        total_views = current_user.views_count

        return render_template('dashboard.html',
                               recent_posts=recent_posts,
                               notifications=notifications,
                               gallery_media=gallery_media,
                               total_followers=total_followers,
                               total_following=total_following,
                               total_posts=total_posts,
                               total_views=total_views)

    @app.route('/profile/edit', methods=['GET', 'POST'])
    @login_required
    def edit_profile():
        """Edit user profile"""
        form = ProfileForm(obj=current_user)

        if form.validate_on_submit():
            current_user.display_name = form.display_name.data
            current_user.bio = form.bio.data
            current_user.location = form.location.data
            current_user.website = form.website.data
            current_user.birth_date = form.birth_date.data

            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('dashboard'))

        return render_template('edit_profile.html', form=form)

    @app.route('/profile/avatar', methods=['POST'])
    @login_required
    def upload_avatar():
        """Upload profile avatar"""
        form = AvatarUploadForm()

        if form.validate_on_submit():
            file = form.avatar.data
            filename = secure_filename(
                f"avatar_{current_user.id}_{secrets.token_hex(8)}.jpg")
            filepath = os.path.join(
                app.config['UPLOAD_FOLDER'], 'avatars', filename)

            # Process and save image
            img = Image.open(file)

            # Convert RGBA to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                rgb_img.paste(
                    img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = rgb_img
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            # Resize to max 400x400 while maintaining aspect ratio
            img.thumbnail((400, 400), Image.Resampling.LANCZOS)

            # Save as JPEG with high quality
            img.save(filepath, 'JPEG', quality=90, optimize=True)

            # Update user with the new avatar path
            current_user.avatar = f'/static/uploads/avatars/{filename}'
            db.session.commit()

            flash('Avatar updated successfully!', 'success')
        else:
            flash('Invalid file. Please upload an image.', 'danger')

        return redirect(url_for('edit_profile'))

    @app.route('/profile/wallpaper', methods=['POST'])
    @login_required
    def upload_wallpaper():
        """Upload profile wallpaper"""
        form = WallpaperUploadForm()

        if form.validate_on_submit():
            file = form.wallpaper.data
            filename = secure_filename(
                f"wallpaper_{current_user.id}_{secrets.token_hex(8)}.jpg")
            filepath = os.path.join(
                app.config['UPLOAD_FOLDER'], 'wallpapers', filename)

            # Process and save image
            img = Image.open(file)

            # Convert RGBA to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                rgb_img.paste(
                    img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = rgb_img
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            # Resize to max 1920x1080 while maintaining aspect ratio
            img.thumbnail((1920, 1080), Image.Resampling.LANCZOS)

            # Save as JPEG with high quality
            img.save(filepath, 'JPEG', quality=85, optimize=True)

            # Update user
            current_user.wallpaper = f'/static/uploads/wallpapers/{filename}'
            db.session.commit()

            flash('Wallpaper updated successfully!', 'success')
        else:
            flash('Invalid file. Please upload an image.', 'danger')

        return redirect(url_for('edit_profile'))

    @app.route('/social/add', methods=['POST'])
    @login_required
    def add_social_link():
        """Add a social media link"""
        form = SocialLinkForm()

        if form.validate_on_submit():
            link = SocialLink(
                user_id=current_user.id,
                platform=form.platform.data,
                url=form.url.data,
                handle=form.handle.data,
                is_premium=(form.platform.data in [
                            'onlyfans', 'fansly', 'allaccessfans'])
            )
            db.session.add(link)
            db.session.commit()

            flash(f'{form.platform.data.title()} link added successfully!', 'success')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'{field}: {error}', 'danger')

        return redirect(url_for('edit_profile'))

    @app.route('/social/delete/<int:link_id>', methods=['POST'])
    @login_required
    def delete_social_link(link_id):
        """Delete a social media link"""
        link = SocialLink.query.get_or_404(link_id)

        if link.user_id != current_user.id:
            abort(403)

        db.session.delete(link)
        db.session.commit()

        flash('Social link deleted successfully!', 'success')
        return redirect(url_for('edit_profile'))

    # ===== GALLERY ROUTES =====
    @app.route('/gallery/upload', methods=['POST'])
    @login_required
    def upload_gallery_media():
        """Upload image or video to gallery"""
        if 'media' not in request.files:
            flash('No file selected', 'danger')
            return redirect(url_for('dashboard'))

        file = request.files['media']
        caption = request.form.get('caption', '')

        if file.filename == '':
            flash('No file selected', 'danger')
            return redirect(url_for('dashboard'))

        # Determine file type
        filename = file.filename.lower()
        is_video = filename.endswith(('.mp4', '.mov', '.avi', '.webm', '.mkv'))
        is_image = filename.endswith(
            ('.jpg', '.jpeg', '.png', '.gif', '.webp'))

        if not (is_video or is_image):
            flash('Invalid file format. Please upload an image or video.', 'danger')
            return redirect(url_for('dashboard'))

        try:
            # Generate unique filename
            file_ext = filename.split('.')[-1]
            unique_filename = secure_filename(
                f"{'video' if is_video else 'image'}_{current_user.id}_{secrets.token_hex(8)}.{file_ext}")
            filepath = os.path.join(
                app.config['UPLOAD_FOLDER'], 'gallery', unique_filename)

            # Get file size
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)

            thumbnail_url = None
            duration = None

            if is_video:
                # Save video file
                file.save(filepath)

                # Try to generate thumbnail (first frame) if moviepy is available
                try:
                    from moviepy.editor import VideoFileClip
                    video = VideoFileClip(filepath)
                    duration = int(video.duration)

                    # Generate thumbnail
                    thumbnail_filename = f"thumb_{unique_filename}.jpg"
                    thumbnail_path = os.path.join(
                        app.config['UPLOAD_FOLDER'], 'gallery', 'thumbnails', thumbnail_filename)
                    os.makedirs(os.path.dirname(thumbnail_path), exist_ok=True)

                    # Save thumbnail (frame at 1 second)
                    video.save_frame(thumbnail_path, t=min(1, duration/2))
                    video.close()

                    thumbnail_url = f'/static/uploads/gallery/thumbnails/{thumbnail_filename}'
                except ImportError:
                    # moviepy not installed, skip thumbnail generation
                    print("moviepy not installed, skipping thumbnail generation")
                except Exception as e:
                    print(f"Error generating video thumbnail: {e}")
            else:
                # Process and save image
                img = Image.open(file)

                # Convert RGBA to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    rgb_img.paste(img, mask=img.split()
                                  [-1] if img.mode == 'RGBA' else None)
                    img = rgb_img
                elif img.mode != 'RGB':
                    img = img.convert('RGB')

                # Resize to max 1200x1200 while maintaining aspect ratio
                img.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
                img.save(filepath, 'JPEG', quality=85, optimize=True)

            # Create gallery entry
            gallery_media = GalleryImage(
                user_id=current_user.id,
                media_url=f'/static/uploads/gallery/{unique_filename}',
                thumbnail_url=thumbnail_url,
                caption=caption,
                media_type='video' if is_video else 'image',
                file_size=file_size,
                duration=duration
            )
            db.session.add(gallery_media)
            db.session.commit()

            flash(
                f'{"Video" if is_video else "Image"} added to gallery successfully!', 'success')

        except Exception as e:
            flash(f'Error uploading file: {str(e)}', 'danger')
            print(f"Upload error: {e}")

        return redirect(url_for('dashboard'))

    @app.route('/gallery/add', methods=['POST'])
    @login_required
    def add_gallery_image():
        """Legacy image upload - redirects to new method"""
        return upload_gallery_media()

    @app.route('/gallery/add-video', methods=['POST'])
    @login_required
    def add_gallery_video():
        """Legacy video upload - redirects to new method"""
        return upload_gallery_media()

    @app.route('/gallery/delete/<int:media_id>', methods=['POST'])
    @login_required
    def delete_gallery_media(media_id):
        """Delete image or video from gallery"""
        try:
            media = GalleryImage.query.get_or_404(media_id)

            # Check ownership
            if media.user_id != current_user.id:
                return jsonify({'error': 'Unauthorized'}), 403

            # Delete the actual file from filesystem
            # Handle both media_url and image_url for backward compatibility
            media_url = getattr(media, 'media_url', None) or getattr(
                media, 'image_url', None)

            if media_url:
                # Extract filename from URL
                filename = media_url.split('/')[-1]
                filepath = os.path.join(
                    app.config['UPLOAD_FOLDER'], 'gallery', filename)

                # Delete main file if it exists
                if os.path.exists(filepath):
                    os.remove(filepath)

                # Delete thumbnail if it exists (for videos)
                if hasattr(media, 'thumbnail_url') and media.thumbnail_url:
                    thumb_filename = media.thumbnail_url.split('/')[-1]
                    thumb_path = os.path.join(
                        app.config['UPLOAD_FOLDER'], 'gallery', 'thumbnails', thumb_filename)
                    if os.path.exists(thumb_path):
                        os.remove(thumb_path)

            # Delete from database
            db.session.delete(media)
            db.session.commit()

            return jsonify({'success': True, 'message': 'Deleted successfully'}), 200

        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    @app.route('/gallery/delete/<int:image_id>', methods=['POST'])
    @login_required
    def delete_gallery_image(image_id):
        """Legacy delete - redirects to new method"""
        return delete_gallery_media(image_id)

    @app.route('/post/create', methods=['POST'])
    @login_required
    def create_post():
        """Create a new post"""
        form = PostForm()

        if form.validate_on_submit():
            media_url = None
            media_type = None

            if form.media.data:
                file = form.media.data
                filename = secure_filename(
                    f"post_{current_user.id}_{secrets.token_hex(8)}")

                # Check if it's video or image
                if file.filename.lower().endswith(('.mp4', '.mov', '.avi')):
                    filename += '.mp4'
                    media_type = 'video'
                    filepath = os.path.join(
                        app.config['UPLOAD_FOLDER'], 'posts', filename)
                    file.save(filepath)
                else:
                    filename += '.jpg'
                    media_type = 'image'
                    filepath = os.path.join(
                        app.config['UPLOAD_FOLDER'], 'posts', filename)

                    # Process image
                    img = Image.open(file)
                    if img.mode in ('RGBA', 'LA', 'P'):
                        rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                        if img.mode == 'P':
                            img = img.convert('RGBA')
                        rgb_img.paste(img, mask=img.split()
                                      [-1] if img.mode == 'RGBA' else None)
                        img = rgb_img
                    elif img.mode != 'RGB':
                        img = img.convert('RGB')

                    img.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
                    img.save(filepath, 'JPEG', quality=85, optimize=True)

                media_url = f'/static/uploads/posts/{filename}'

            post = Post(
                user_id=current_user.id,
                content=form.content.data,
                media_url=media_url,
                media_type=media_type
            )
            db.session.add(post)
            db.session.commit()

            flash('Post created successfully!', 'success')
        else:
            flash('Error creating post. Please try again.', 'danger')

        return redirect(url_for('dashboard'))

    @app.route('/post/<int:post_id>/like', methods=['POST'])
    @login_required
    def like_post(post_id):
        """Like a post"""
        post = Post.query.get_or_404(post_id)
        post.likes += 1

        # Create notification for post author
        if post.user_id != current_user.id:
            notification = Notification(
                user_id=post.user_id,
                type='like',
                message=f'{current_user.display_name or current_user.username} liked your post',
                link=f'/post/{post_id}'
            )
            db.session.add(notification)

        db.session.commit()

        return jsonify({'likes': post.likes})

    @app.route('/post/<int:post_id>/comment', methods=['POST'])
    @login_required
    def add_comment(post_id):
        """Add comment to post"""
        post = Post.query.get_or_404(post_id)
        content = request.json.get('content')

        if content:
            comment = Comment(
                user_id=current_user.id,
                post_id=post_id,
                content=content
            )
            db.session.add(comment)

            # Create notification for post author
            if post.user_id != current_user.id:
                notification = Notification(
                    user_id=post.user_id,
                    type='comment',
                    message=f'{current_user.display_name or current_user.username} commented on your post',
                    link=f'/post/{post_id}'
                )
                db.session.add(notification)

            db.session.commit()

            return jsonify({
                'success': True,
                'comment': {
                    'id': comment.id,
                    'content': comment.content,
                    'author': current_user.display_name or current_user.username,
                    'avatar': current_user.avatar,
                    'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M')
                }
            })

        return jsonify({'success': False}), 400

    @app.route('/follow/<int:user_id>', methods=['POST'])
    @login_required
    def follow_user(user_id):
        """Follow/unfollow a user"""
        if user_id == current_user.id:
            return jsonify({'error': 'Cannot follow yourself'}), 400

        user = User.query.get_or_404(user_id)
        follow = Follow.query.filter_by(
            follower_id=current_user.id,
            followed_id=user_id
        ).first()

        if follow:
            # Unfollow
            db.session.delete(follow)
            user.followers_count -= 1
            action = 'unfollowed'
        else:
            # Follow
            follow = Follow(
                follower_id=current_user.id,
                followed_id=user_id
            )
            db.session.add(follow)
            user.followers_count += 1
            action = 'followed'

            # Create notification
            notification = Notification(
                user_id=user_id,
                type='follow',
                message=f'{current_user.display_name or current_user.username} started following you',
                link=f'/creator/{current_user.username}'
            )
            db.session.add(notification)

        db.session.commit()

        return jsonify({
            'action': action,
            'followers': user.followers_count
        })

    @app.route('/search')
    def search():
        """Global search - Only show approved users"""
        form = SearchForm()
        query = request.args.get('q', '')

        if query and len(query) >= 2:
            # Search users (only approved)
            users = User.query.filter(
                db.and_(
                    User.is_active == True,
                    User.is_approved == True,
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

            return render_template('search_results.html',
                                   query=query,
                                   users=users,
                                   posts=posts)

        return render_template('search.html', form=form)

    @app.route('/verify', methods=['GET', 'POST'])
    @login_required
    def request_verification():
        """Request account verification"""
        if current_user.is_verified:
            flash('Your account is already verified!', 'info')
            return redirect(url_for('dashboard'))

        # Check if already has pending request
        existing = VerificationRequest.query.filter_by(
            user_id=current_user.id,
            status='pending'
        ).first()

        if existing:
            flash('You already have a pending verification request.', 'warning')
            return redirect(url_for('dashboard'))

        form = VerificationRequestForm()

        if form.validate_on_submit():
            # Save ID proof
            id_file = form.id_proof.data
            id_filename = secure_filename(
                f"id_{current_user.id}_{secrets.token_hex(8)}.jpg")
            id_filepath = os.path.join(
                app.config['UPLOAD_FOLDER'], 'verification', id_filename)
            id_file.save(id_filepath)

            # Save selfie
            selfie_file = form.selfie.data
            selfie_filename = secure_filename(
                f"selfie_{current_user.id}_{secrets.token_hex(8)}.jpg")
            selfie_filepath = os.path.join(
                app.config['UPLOAD_FOLDER'], 'verification', selfie_filename)
            selfie_file.save(selfie_filepath)

            # Create request
            verification_request = VerificationRequest(
                user_id=current_user.id,
                id_proof=f'/static/uploads/verification/{id_filename}',
                selfie=f'/static/uploads/verification/{selfie_filename}',
                notes=form.notes.data
            )
            db.session.add(verification_request)
            db.session.commit()

            flash(
                'Verification request submitted! We\'ll review it within 24-48 hours.', 'success')
            return redirect(url_for('dashboard'))

        return render_template('verify.html', form=form)

    @app.route('/notifications')
    @login_required
    def notifications():
        """View all notifications"""
        page = request.args.get('page', 1, type=int)
        per_page = 20

        pagination = Notification.query.filter_by(user_id=current_user.id)\
            .order_by(Notification.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)

        notifications = pagination.items

        # Mark all as read
        for notification in notifications:
            if not notification.is_read:
                notification.is_read = True
        db.session.commit()

        return render_template('notifications.html',
                               notifications=notifications,
                               pagination=pagination)

    @app.route('/submit', methods=['GET', 'POST'])
    def submit_profile():
        """Submit profile for listing (public form)"""
        if request.method == 'POST':
            flash('Thank you for your submission! We\'ll review it shortly.', 'success')
            return redirect(url_for('index'))

        return render_template('submit.html')

    @app.route('/contact', methods=['GET', 'POST'])
    def contact():
        """Contact page"""
        form = ContactForm()

        if form.validate_on_submit():
            flash('Thank you for your message! We\'ll get back to you soon.', 'success')
            return redirect(url_for('index'))

        return render_template('contact.html', form=form)

    # Register error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403

    # Register context processors
    # Register context processors
    @app.context_processor
    def utility_processor():
        def pluralize(count, singular, plural=None):
            if not plural:
                plural = singular + 's'
            return singular if count == 1 else plural

        # Remove time_ago from here since we're using a filter
        return dict(pluralize=pluralize)

    return app


# Create the app instance
app = create_app(os.getenv('FLASK_CONFIG') or 'default')

if __name__ == '__main__':
    app.run(debug=True)
