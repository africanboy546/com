from flask import Blueprint, jsonify, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime, timedelta

from models import db, User, VerificationRequest, Post, Comment, Notification, AdminLog

admin = Blueprint('admin', __name__)


def admin_required(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


@admin.route('/')
@login_required
@admin_required
def dashboard():
    """Admin dashboard with comprehensive stats and real-time data"""

    # ===== BASIC COUNTS =====
    total_users = User.query.count()
    verified_users = User.query.filter_by(is_verified=True).count()
    pending_verifications = VerificationRequest.query.filter_by(
        status='pending').count()
    total_posts = Post.query.count()
    total_comments = Comment.query.count()

    # ===== APPROVAL STATS =====
    pending_approval = User.query.filter_by(
        is_approved=False, is_active=True).count()
    approved_users = User.query.filter_by(is_approved=True).count()

    # ===== RESTRICTION STATS =====
    restricted_users = User.query.filter_by(is_restricted=True).count()

    # ===== FEATURED STATS =====
    featured_users = User.query.filter_by(is_featured=True).count()

    # ===== TODAY'S STATS =====
    today = datetime.utcnow().date()
    new_users_today = User.query.filter(User.created_at >= today).count()
    new_posts_today = Post.query.filter(Post.created_at >= today).count()
    new_comments_today = Comment.query.filter(
        Comment.created_at >= today).count()

    # ===== PENDING USERS LIST =====
    pending_users = User.query.filter_by(is_approved=False, is_active=True)\
        .order_by(User.created_at.desc()).limit(10).all()

    # ===== RECENT USERS =====
    recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()

    # ===== RECENT VERIFICATION REQUESTS =====
    verification_requests = VerificationRequest.query.filter_by(status='pending')\
        .order_by(VerificationRequest.submitted_at.desc()).limit(10).all()

    # ===== GROWTH DATA FOR CHART (LAST 30 DAYS) =====
    growth_dates = []
    growth_counts = []

    for i in range(30, 0, -1):
        date = (datetime.utcnow() - timedelta(days=i)).date()
        growth_dates.append(date.strftime('%m/%d'))
        count = User.query.filter(
            User.created_at <= date + timedelta(days=1)).count()
        growth_counts.append(count)

    # ===== RECENT ACTIVITIES =====
    recent_activities = []

    # Add new user registrations
    new_users = User.query.order_by(User.created_at.desc()).limit(3).all()
    for user in new_users:
        recent_activities.append({
            'type': 'user',
            'icon': 'user-plus',
            'title': f'New user registered: {user.display_name or user.username}',
            'user': user.username,
            'created_at': user.created_at
        })

    # Add verification requests
    new_verifications = VerificationRequest.query.order_by(
        VerificationRequest.submitted_at.desc()).limit(2).all()
    for verif in new_verifications:
        user = User.query.get(verif.user_id)
        if user:
            recent_activities.append({
                'type': 'verify',
                'icon': 'id-card',
                'title': f'Verification request from @{user.username}',
                'user': user.username,
                'created_at': verif.submitted_at
            })

    # Add new posts
    new_posts = Post.query.order_by(Post.created_at.desc()).limit(2).all()
    for post in new_posts:
        user = User.query.get(post.user_id)
        if user:
            recent_activities.append({
                'type': 'post',
                'icon': 'pen',
                'title': f'New post by @{user.username}',
                'user': user.username,
                'created_at': post.created_at
            })

    # Sort activities by date (newest first)
    recent_activities.sort(key=lambda x: x['created_at'], reverse=True)
    recent_activities = recent_activities[:8]  # Keep only 8 most recent

    # ===== ADMIN ACTION LOGS =====
    admin_logs = AdminLog.query.order_by(
        AdminLog.timestamp.desc()).limit(5).all()

    # Format admin logs for template
    formatted_logs = []
    for log in admin_logs:
        admin_user = User.query.get(log.admin_id)
        action_icon = 'user-check'  # Default icon
        if 'approve' in log.action.lower():
            action_icon = 'check-circle'
        elif 'restrict' in log.action.lower():
            action_icon = 'ban'
        elif 'delete' in log.action.lower():
            action_icon = 'trash'
        elif 'verify' in log.action.lower():
            action_icon = 'check-double'

        formatted_logs.append({
            'action_icon': action_icon,
            'action': log.action,
            'admin_name': admin_user.username if admin_user else 'Unknown',
            'timestamp': log.timestamp
        })

    # ===== PLATFORM HEALTH METRICS =====
    # Calculate storage used (simplified - you'd need to sum file sizes)
    storage_used = 45  # Placeholder - implement actual calculation

    # Calculate average response time (placeholder)
    response_time = 234  # Placeholder - implement actual monitoring

    # ===== VIEWS STATS =====
    total_views = db.session.query(db.func.sum(User.views_count)).scalar() or 0
    total_views_k = round(total_views / 1000, 1)

    # ===== API CALLS TODAY (placeholder) =====
    api_calls_today = 1250  # You'll need to implement API call tracking

    # ===== ACTIVE USERS TODAY =====
    active_users = User.query.filter(User.last_seen >= today).count()

    # ===== URGENT COUNTS =====
    pending_urgent = min(pending_approval, 3)  # Just for display

    # Reports (you'll need a Report model for this)
    urgent_reports = 0
    total_reports = 0

    return render_template('admin/dashboard.html',
                           # Basic counts
                           total_users=total_users,
                           verified_users=verified_users,
                           pending_verifications=pending_verifications,
                           total_posts=total_posts,
                           total_comments=total_comments,

                           # Approval stats
                           pending_approval=pending_approval,
                           approved_users=approved_users,

                           # Restriction stats
                           restricted_users=restricted_users,

                           # Featured stats
                           featured_users=featured_users,

                           # Today's stats
                           new_users_today=new_users_today,
                           new_posts_today=new_posts_today,
                           new_comments_today=new_comments_today,

                           # User lists
                           pending_users=pending_users,
                           recent_users=recent_users,
                           verification_requests=verification_requests,

                           # Chart data
                           growth_dates=growth_dates,
                           growth_counts=growth_counts,

                           # Activity data
                           recent_activities=recent_activities,
                           admin_logs=formatted_logs,

                           # Health metrics
                           storage_used=storage_used,
                           response_time=response_time,

                           # Other stats
                           total_views=total_views_k,
                           api_calls_today=api_calls_today,
                           active_users=active_users,

                           # Urgent counts
                           pending_urgent=pending_urgent,
                           urgent_reports=urgent_reports,
                           total_reports=total_reports)


@admin.route('/users')
@login_required
@admin_required
def users():
    """Manage users"""
    page = request.args.get('page', 1, type=int)
    per_page = 20

    search = request.args.get('q', '')
    filter_by = request.args.get('filter', 'all')
    sort_by = request.args.get('sort', 'newest')

    query = User.query

    if search:
        query = query.filter(
            db.or_(
                User.username.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%'),
                User.display_name.ilike(f'%{search}%')
            )
        )

    if filter_by == 'verified':
        query = query.filter_by(is_verified=True)
    elif filter_by == 'unverified':
        query = query.filter_by(is_verified=False)
    elif filter_by == 'admin':
        query = query.filter_by(is_admin=True)
    elif filter_by == 'inactive':
        query = query.filter_by(is_active=False)
    elif filter_by == 'pending':
        query = query.filter_by(is_approved=False, is_active=True)
    elif filter_by == 'approved':
        query = query.filter_by(is_approved=True)
    elif filter_by == 'restricted':
        query = query.filter_by(is_restricted=True)
    elif filter_by == 'featured':
        query = query.filter_by(is_featured=True)

    # Sorting
    if sort_by == 'oldest':
        query = query.order_by(User.created_at.asc())
    elif sort_by == 'followers':
        query = query.order_by(User.followers_count.desc())
    elif sort_by == 'views':
        query = query.order_by(User.views_count.desc())
    else:  # newest
        query = query.order_by(User.created_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    users = pagination.items

    return render_template('admin/users.html',
                           users=users,
                           pagination=pagination,
                           search=search,
                           filter_by=filter_by,
                           sort_by=sort_by)


@admin.route('/user/<int:user_id>/toggle-verify', methods=['POST'])
@login_required
@admin_required
def toggle_verify(user_id):
    """Toggle user verification status"""
    user = User.query.get_or_404(user_id)
    user.is_verified = not user.is_verified
    db.session.commit()

    # Log the action
    log = AdminLog(
        admin_id=current_user.id,
        action=f"{'Verified' if user.is_verified else 'Unverified'} user @{user.username}",
        target_id=user.id,
        timestamp=datetime.utcnow()
    )
    db.session.add(log)
    db.session.commit()

    flash(f'User {user.username} verification status updated.', 'success')
    return redirect(url_for('admin.users'))


@admin.route('/user/<int:user_id>/toggle-feature', methods=['POST'])
@login_required
@admin_required
def toggle_feature(user_id):
    """Toggle user featured status"""
    user = User.query.get_or_404(user_id)
    user.is_featured = not user.is_featured
    db.session.commit()

    # Log the action
    log = AdminLog(
        admin_id=current_user.id,
        action=f"{'Featured' if user.is_featured else 'Unfeatured'} user @{user.username}",
        target_id=user.id,
        timestamp=datetime.utcnow()
    )
    db.session.add(log)
    db.session.commit()

    flash(f'User {user.username} featured status updated.', 'success')
    return redirect(url_for('admin.users'))


@admin.route('/user/<int:user_id>/toggle-active', methods=['POST'])
@login_required
@admin_required
def toggle_active(user_id):
    """Toggle user active status"""
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()

    status = 'activated' if user.is_active else 'deactivated'

    # Log the action
    log = AdminLog(
        admin_id=current_user.id,
        action=f"{status.capitalize()} user @{user.username}",
        target_id=user.id,
        timestamp=datetime.utcnow()
    )
    db.session.add(log)
    db.session.commit()

    flash(f'User {user.username} {status}.', 'success')
    return redirect(url_for('admin.users'))


@admin.route('/verifications')
@login_required
@admin_required
def verifications():
    """Manage verification requests"""
    page = request.args.get('page', 1, type=int)
    per_page = 20

    status = request.args.get('status', 'pending')

    query = VerificationRequest.query.filter_by(status=status)

    pagination = query.order_by(VerificationRequest.submitted_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)

    requests = pagination.items

    return render_template('admin/verifications.html',
                           requests=requests,
                           pagination=pagination,
                           status=status)


@admin.route('/verification/<int:request_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_verification(request_id):
    """Approve verification request"""
    verification = VerificationRequest.query.get_or_404(request_id)
    verification.status = 'approved'
    verification.reviewed_at = datetime.utcnow()
    verification.reviewed_by = current_user.id

    # Verify user
    user = User.query.get(verification.user_id)
    user.is_verified = True

    # Log the action
    log = AdminLog(
        admin_id=current_user.id,
        action=f"Approved verification for @{user.username}",
        target_id=user.id,
        timestamp=datetime.utcnow()
    )
    db.session.add(log)

    # Send notification to user
    notification = Notification(
        user_id=user.id,
        type='verification',
        message='Your identity verification has been approved!',
        link=url_for('creator_profile', username=user.username)
    )
    db.session.add(notification)

    db.session.commit()

    flash('Verification request approved.', 'success')
    return redirect(url_for('admin.verifications'))


@admin.route('/verification/<int:request_id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_verification(request_id):
    """Reject verification request"""
    verification = VerificationRequest.query.get_or_404(request_id)
    verification.status = 'rejected'
    verification.reviewed_at = datetime.utcnow()
    verification.reviewed_by = current_user.id

    user = User.query.get(verification.user_id)

    # Log the action
    log = AdminLog(
        admin_id=current_user.id,
        action=f"Rejected verification for @{user.username}",
        target_id=user.id,
        timestamp=datetime.utcnow()
    )
    db.session.add(log)

    # Send notification to user
    notification = Notification(
        user_id=user.id,
        type='verification',
        message='Your identity verification was rejected. Please contact support.',
        link=url_for('contact')
    )
    db.session.add(notification)

    db.session.commit()

    flash('Verification request rejected.', 'warning')
    return redirect(url_for('admin.verifications'))


@admin.route('/user/<int:user_id>/toggle_approval', methods=['POST'])
@login_required
@admin_required
def toggle_approval(user_id):
    """Toggle user approval status"""
    user = User.query.get_or_404(user_id)
    user.is_approved = not user.is_approved
    db.session.commit()

    # Log the action
    log = AdminLog(
        admin_id=current_user.id,
        action=f"{'Approved' if user.is_approved else 'Unapproved'} user @{user.username}",
        target_id=user.id,
        timestamp=datetime.utcnow()
    )
    db.session.add(log)

    # Send notification to user
    if user.is_approved:
        notification = Notification(
            user_id=user_id,
            type='approval',
            message='Your account has been approved! You can now access all features.',
            link=url_for('dashboard')
        )
        db.session.add(notification)
    db.session.commit()

    flash(f'User {user.username} approval status updated.', 'success')
    return redirect(url_for('admin.users'))


@admin.route('/user/<int:user_id>/toggle_restriction', methods=['POST'])
@login_required
@admin_required
def toggle_restriction(user_id):
    """Toggle user restriction status"""
    user = User.query.get_or_404(user_id)
    user.is_restricted = not user.is_restricted

    if user.is_restricted:
        user.restricted_at = datetime.utcnow()
        user.restricted_by = current_user.id
    else:
        user.restriction_lifted_at = datetime.utcnow()
        user.restriction_lifted_by = current_user.id

    db.session.commit()

    # Log the action
    log = AdminLog(
        admin_id=current_user.id,
        action=f"{'Restricted' if user.is_restricted else 'Lifted restriction for'} user @{user.username}",
        target_id=user.id,
        timestamp=datetime.utcnow()
    )
    db.session.add(log)

    flash(f'User {user.username} restriction status updated.', 'success')
    return redirect(url_for('admin.users'))


@admin.route('/user/<int:user_id>/quick-approve', methods=['POST'])
@login_required
@admin_required
def quick_approve(user_id):
    """Quick approve a user"""
    user = User.query.get_or_404(user_id)
    user.is_approved = True
    db.session.commit()

    # Log the action
    log = AdminLog(
        admin_id=current_user.id,
        action=f"Quick-approved user @{user.username}",
        target_id=user.id,
        timestamp=datetime.utcnow()
    )
    db.session.add(log)

    return jsonify({'success': True})


@admin.route('/user/<int:user_id>/restrict', methods=['POST'])
@login_required
@admin_required
def restrict_user(user_id):
    """Restrict a user with reason"""
    data = request.get_json()
    user = User.query.get_or_404(user_id)

    user.is_restricted = True
    user.restriction_reason = data.get('reason')
    user.restriction_duration = data.get('duration')
    user.restriction_notes = data.get('notes')
    user.restricted_at = datetime.utcnow()
    user.restricted_by = current_user.id

    db.session.commit()

    # Log the action
    log = AdminLog(
        admin_id=current_user.id,
        action=f"Restricted user @{user.username} - Reason: {data.get('reason')}",
        target_id=user.id,
        timestamp=datetime.utcnow()
    )
    db.session.add(log)

    # Create notification for user
    notification = Notification(
        user_id=user_id,
        type='restriction',
        message=f'Your account has been restricted. Reason: {data.get("reason")}',
        link=url_for('contact')
    )
    db.session.add(notification)
    db.session.commit()

    return jsonify({'success': True})


@admin.route('/user/<int:user_id>/lift-restriction', methods=['POST'])
@login_required
@admin_required
def lift_restriction(user_id):
    """Lift restriction from user"""
    user = User.query.get_or_404(user_id)

    user.is_restricted = False
    user.restriction_reason = None
    user.restriction_lifted_at = datetime.utcnow()
    user.restriction_lifted_by = current_user.id

    db.session.commit()

    # Log the action
    log = AdminLog(
        admin_id=current_user.id,
        action=f"Lifted restriction for user @{user.username}",
        target_id=user.id,
        timestamp=datetime.utcnow()
    )
    db.session.add(log)

    return jsonify({'success': True})


@admin.route('/reports')
@login_required
@admin_required
def reports():
    """View and manage reported content"""
    page = request.args.get('page', 1, type=int)
    per_page = 20

    # You'll need a Report model for this
    # For now, return a template with placeholder data
    return render_template('admin/reports.html', page=page, per_page=per_page)


@admin.route('/bulk-action', methods=['POST'])
@login_required
@admin_required
def bulk_action():
    """Handle bulk actions on users"""
    data = request.get_json()
    action = data.get('action')
    user_ids = data.get('users', [])

    if not user_ids:
        return jsonify({'error': 'No users selected'}), 400

    try:
        action_verb = ""
        if action == 'approve':
            User.query.filter(User.id.in_(user_ids)).update(
                {User.is_approved: True}, synchronize_session=False)
            action_verb = "Approved"
        elif action == 'verify':
            User.query.filter(User.id.in_(user_ids)).update(
                {User.is_verified: True}, synchronize_session=False)
            action_verb = "Verified"
        elif action == 'feature':
            User.query.filter(User.id.in_(user_ids)).update(
                {User.is_featured: True}, synchronize_session=False)
            action_verb = "Featured"
        elif action == 'restrict':
            User.query.filter(User.id.in_(user_ids)).update(
                {User.is_restricted: True, User.restricted_at: datetime.utcnow(
                ), User.restricted_by: current_user.id},
                synchronize_session=False)
            action_verb = "Restricted"
        elif action == 'activate':
            User.query.filter(User.id.in_(user_ids)).update(
                {User.is_active: True}, synchronize_session=False)
            action_verb = "Activated"
        elif action == 'deactivate':
            User.query.filter(User.id.in_(user_ids)).update(
                {User.is_active: False}, synchronize_session=False)
            action_verb = "Deactivated"
        elif action == 'delete':
            User.query.filter(User.id.in_(user_ids)).delete(
                synchronize_session=False)
            action_verb = "Deleted"

        db.session.commit()

        # Log the bulk action
        log = AdminLog(
            admin_id=current_user.id,
            action=f"Bulk {action_verb} {len(user_ids)} users",
            details=f"User IDs: {user_ids}",
            timestamp=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()

        return jsonify({'success': True})

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@admin.route('/api/recent-activity')
@login_required
@admin_required
def recent_activity():
    """API endpoint for recent activity (for AJAX refresh)"""
    activities = []

    # Get recent users
    recent_users = User.query.order_by(User.created_at.desc()).limit(3).all()
    for user in recent_users:
        activities.append({
            'type': 'user',
            'icon': 'user-plus',
            'title': f'New user registered: {user.display_name or user.username}',
            'user': user.username,
            'time': time_ago(user.created_at)
        })

    # Get recent posts
    recent_posts = Post.query.order_by(Post.created_at.desc()).limit(3).all()
    for post in recent_posts:
        user = User.query.get(post.user_id)
        if user:
            activities.append({
                'type': 'post',
                'icon': 'pen',
                'title': f'New post by @{user.username}',
                'user': user.username,
                'time': time_ago(post.created_at)
            })

    return jsonify(activities[:8])


@admin.route('/api/stats')
@login_required
@admin_required
def api_stats():
    """API endpoint for real-time stats"""
    today = datetime.utcnow().date()

    stats = {
        'total_users': User.query.count(),
        'pending_approval': User.query.filter_by(is_approved=False, is_active=True).count(),
        'pending_verifications': VerificationRequest.query.filter_by(status='pending').count(),
        'total_reports': 0,  # You'll need a Report model for this
        'active_users': User.query.filter(User.last_seen >= today).count(),
        'new_posts_today': Post.query.filter(Post.created_at >= today).count(),
    }
    return jsonify(stats)


def time_ago(dt):
    """Helper function to format time ago"""
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
