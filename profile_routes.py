# profile_routes.py
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
import re

from models import db, User

profile_bp = Blueprint('profile', __name__)


@profile_bp.route('/check-username', methods=['POST'])
@login_required
def check_username():
    data = request.get_json()
    username = data.get('username')

    # Check if username exists and isn't current user
    user = User.query.filter_by(username=username).first()
    available = user is None or user.id == current_user.id

    return jsonify({'available': available})


@profile_bp.route('/check-email', methods=['POST'])
@login_required
def check_email():
    data = request.get_json()
    email = data.get('email')

    # Check if email exists and isn't current user
    user = User.query.filter_by(email=email).first()
    available = user is None or user.id == current_user.id

    return jsonify({'available': available})


@profile_bp.route('/update-username', methods=['POST'])
@login_required
def update_username():
    data = request.get_json()
    new_username = data.get('username')

    # Validate username
    if not re.match(r'^[a-zA-Z0-9_]{3,30}$', new_username):
        return jsonify({'success': False, 'error': 'Invalid username format'})

    # Check if taken
    existing = User.query.filter_by(username=new_username).first()
    if existing and existing.id != current_user.id:
        return jsonify({'success': False, 'error': 'Username already taken'})

    current_user.username = new_username
    db.session.commit()

    return jsonify({'success': True})


@profile_bp.route('/update-email', methods=['POST'])
@login_required
def update_email():
    data = request.get_json()
    new_email = data.get('email')

    # Validate email
    if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', new_email):
        return jsonify({'success': False, 'error': 'Invalid email format'})

    # Check if taken
    existing = User.query.filter_by(email=new_email).first()
    if existing and existing.id != current_user.id:
        return jsonify({'success': False, 'error': 'Email already registered'})

    current_user.email = new_email
    db.session.commit()

    return jsonify({'success': True})


@profile_bp.route('/update-password', methods=['POST'])
@login_required
def update_password():
    data = request.get_json()
    current_password = data.get('current_password')
    new_password = data.get('new_password')

    # Verify current password
    if not current_user.verify_password(current_password):
        return jsonify({'success': False, 'error': 'Current password is incorrect'})

    # Validate new password strength
    if len(new_password) < 8:
        return jsonify({'success': False, 'error': 'Password must be at least 8 characters'})

    # Update password
    current_user.password = new_password
    db.session.commit()

    return jsonify({'success': True})
