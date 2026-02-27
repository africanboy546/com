from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.urls import url_parse as url_parse

from models import db, User, Notification
from forms import LoginForm, RegistrationForm

auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user is None or not user.verify_password(form.password.data):
            flash('Invalid username or password.', 'danger')
            return redirect(url_for('auth.login'))

        if not user.is_active:
            flash('This account has been deactivated. Please contact support.', 'warning')
            return redirect(url_for('auth.login'))

        login_user(user, remember=form.remember_me.data)

        # Update last seen
        user.last_seen = db.func.now()
        db.session.commit()

        # Redirect to next page or dashboard
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('dashboard')

        flash(
            f'Welcome back, {user.display_name or user.username}!', 'success')
        return redirect(next_page)

    return render_template('auth/login.html', form=form)


@auth.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    form = RegistrationForm()

    if form.validate_on_submit():
        # Check if username exists
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already taken. Please choose another.', 'danger')
            return render_template('auth/register.html', form=form)

        # Check if email exists
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered. Please use another or login.', 'danger')
            return render_template('auth/register.html', form=form)

        # Create new user - set is_approved to False by default
        user = User(
            username=form.username.data,
            email=form.email.data,
            display_name=form.username.data,  # Default to username
            is_approved=False,  # IMPORTANT: Require admin approval
            is_active=True
        )
        user.password = form.password.data

        db.session.add(user)
        db.session.commit()

        # Create welcome notification
        notification = Notification(
            user_id=user.id,
            type='welcome',
            message='Welcome to VelvetSignals! Your account is pending admin approval. You\'ll be notified once approved.',
            link=url_for('dashboard')
        )
        db.session.add(notification)
        db.session.commit()

        # Log user in but they won't see their profile publicly until approved
        login_user(user)

        flash('Account created successfully! Your profile is pending admin approval. You\'ll be notified once approved.', 'success')
        return redirect(url_for('dashboard'))

    return render_template('auth/register.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


@auth.route('/forgot-password')
def forgot_password():
    """Password reset request"""
    # Implementation would go here
    flash('Password reset functionality coming soon!', 'info')
    return redirect(url_for('auth.login'))

