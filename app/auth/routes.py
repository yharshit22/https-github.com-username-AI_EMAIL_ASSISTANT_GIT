import logging
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from app import db
from app.auth import bp
from app.models import User
from app.auth.forms import LoginForm, RegistrationForm

logger = logging.getLogger(__name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password', 'danger')
            logger.warning(f"Failed login attempt for email: {form.email.data}")
            return redirect(url_for('auth.login'))
        
        if not user.is_active:
            flash('Your account has been deactivated. Please contact support.', 'warning')
            return redirect(url_for('auth.login'))
        
        # Log user in
        login_user(user, remember=form.remember_me.data)
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Log successful login
        logger.info(f"User {user.email} logged in successfully")
        
        # Redirect to next page or dashboard
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.dashboard')
        
        flash('Welcome back!', 'success')
        return redirect(next_page)
    
    return render_template('auth/login.html', title='Sign In', form=form)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Create new user
        user = User(
            username=form.username.data,
            email=form.email.data.lower()
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        logger.info(f"New user registered: {user.email}")
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', title='Register', form=form)

@bp.route('/logout')
@login_required
def logout():
    """Handle user logout"""
    user_email = current_user.email
    logout_user()
    logger.info(f"User {user_email} logged out")
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))

@bp.route('/profile')
@login_required
def profile():
    """Show user profile"""
    return render_template('auth/profile.html', title='Profile', user=current_user)

@bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Handle password change"""
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.old_password.data):
            flash('Current password is incorrect.', 'danger')
            return redirect(url_for('auth.change_password'))
        
        current_user.set_password(form.new_password.data)
        db.session.commit()
        
        logger.info(f"User {current_user.email} changed password")
        flash('Your password has been updated.', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/change_password.html', title='Change Password', form=form)

# Import forms after routes to avoid circular imports
from app.auth.forms import ChangePasswordForm
from datetime import datetime