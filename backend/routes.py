from flask import render_template, request, redirect, url_for, flash, session, send_file
from flask_login import login_required, current_user, logout_user
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import mimetypes

from backend.app import app, db
from backend.models import User, File, Banner, BanLog
from backend.auth import admin_required
from backend.config import Config

# ========== PUBLIC ROUTES ==========

@app.route('/')
def index():
    """Home page"""
    banner = Banner.query.first()
    banner_url = banner.image_url if banner else '/static/images/banner-default.jpg'
    return render_template('index.html', banner_url=banner_url)

@app.route('/banned')
def banned():
    """Banned page"""
    return render_template('banned.html')

@app.route('/logout')
@login_required
def logout():
    """Logout user"""
    logout_user()
    session.clear()
    return redirect(url_for('index'))

# ========== USER ROUTES ==========

@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard"""
    if current_user.is_banned:
        flash('Your account has been banned!', 'error')
        return redirect(url_for('banned'))
    
    files = File.query.filter_by(user_id=current_user.id).order_by(File.uploaded_at.desc()).all()
    file_count = len(files)
    return render_template('dashboard.html', user=current_user, files=files, file_count=file_count)

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    """Upload file"""
    if current_user.is_banned:
        flash('Your account is banned!', 'error')
        return redirect(url_for('banned'))
    
    if 'file' not in request.files:
        flash('No file selected!', 'error')
        return redirect(url_for('dashboard'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected!', 'error')
        return redirect(url_for('dashboard'))
    
    # Check file extension
    allowed_extensions = {'py', 'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'zip', 'rar', 'html', 'css', 'js', 'json', 'xml', 'csv'}
    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    
    if ext not in allowed_extensions:
        flash(f'File type .{ext} is not allowed!', 'error')
        return redirect(url_for('dashboard'))
    
    # Save file
    original_filename = file.filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    secure_name = secure_filename(f"{timestamp}_{original_filename}")
    file_path = os.path.join(Config.UPLOAD_FOLDER, secure_name)
    file.save(file_path)
    
    # Get file size
    file_size = os.path.getsize(file_path)
    file_type = ext if ext else 'unknown'
    
    # Save to database
    new_file = File(
        filename=secure_name,
        original_filename=original_filename,
        file_path=file_path,
        file_size=file_size,
        file_type=file_type,
        user_id=current_user.id
    )
    db.session.add(new_file)
    db.session.commit()
    
    flash(f'File "{original_filename}" uploaded successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/download/<int:file_id>')
@login_required
def download_file(file_id):
    """Download file"""
    file = File.query.get_or_404(file_id)
    
    # Check permission
    if file.user_id != current_user.id and not current_user.is_admin:
        flash('Access denied!', 'error')
        return redirect(url_for('dashboard'))
    
    # Check if file exists
    if not os.path.exists(file.file_path):
        flash('File not found on server!', 'error')
        return redirect(url_for('dashboard'))
    
    # Get mime type
    mime_type = mimetypes.guess_type(file.original_filename)[0] or 'application/octet-stream'
    
    return send_file(
        file.file_path, 
        as_attachment=True, 
        download_name=file.original_filename,
        mimetype=mime_type
    )

@app.route('/delete-file/<int:file_id>', methods=['POST'])
@login_required
def delete_file(file_id):
    """Delete file"""
    file = File.query.get_or_404(file_id)
    
    # Check permission
    if file.user_id != current_user.id and not current_user.is_admin:
        flash('Access denied!', 'error')
        return redirect(url_for('dashboard'))
    
    # Delete file from filesystem
    if os.path.exists(file.file_path):
        os.remove(file.file_path)
    
    # Delete from database
    db.session.delete(file)
    db.session.commit()
    
    flash(f'File "{file.original_filename}" deleted successfully!', 'success')
    return redirect(url_for('dashboard'))

# ========== ADMIN ROUTES ==========

@app.route('/admin-panel')
@login_required
@admin_required
def admin_panel():
    """Admin panel"""
    users = User.query.order_by(User.created_at.desc()).all()
    banned_count = User.query.filter_by(is_banned=True).count()
    total_files = File.query.count()
    banner = Banner.query.first()
    banner_url = banner.image_url if banner else '/static/images/banner-default.jpg'
    
    # Get ban logs
    ban_logs = BanLog.query.order_by(BanLog.created_at.desc()).limit(20).all()
    
    return render_template(
        'admin-panel.html', 
        users=users, 
        banned_count=banned_count,
        total_files=total_files,
        banner_url=banner_url,
        ban_logs=ban_logs
    )

@app.route('/admin/create-user', methods=['POST'])
@login_required
@admin_required
def admin_create_user():
    """Create new user from admin panel"""
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    email = request.form.get('email', '').strip()
    ram = int(request.form.get('ram', 20))
    cpu = int(request.form.get('cpu', 100))
    
    # Validation
    if not username or not password:
        flash('Username and password are required!', 'error')
        return redirect(url_for('admin_panel'))
    
    if len(username) < 3:
        flash('Username must be at least 3 characters!', 'error')
        return redirect(url_for('admin_panel'))
    
    if len(password) < 4:
        flash('Password must be at least 4 characters!', 'error')
        return redirect(url_for('admin_panel'))
    
    # Check if username exists
    if User.query.filter_by(username=username).first():
        flash(f'Username "{username}" already exists!', 'error')
        return redirect(url_for('admin_panel'))
    
    # Check if email exists
    if email and User.query.filter_by(email=email).first():
        flash(f'Email "{email}" already exists!', 'error')
        return redirect(url_for('admin_panel'))
    
    # Create user
    from werkzeug.security import generate_password_hash
    hashed_password = generate_password_hash(password)
    
    user = User(
        username=username,
        password=hashed_password,
        email=email if email else None,
        ram=ram,
        cpu=cpu,
        is_admin=False,
        is_banned=False
    )
    db.session.add(user)
    db.session.commit()
    
    flash(f'User "{username}" created successfully with {ram}GB RAM & {cpu}% CPU!', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/ban-user', methods=['POST'])
@login_required
@admin_required
def admin_ban_user():
    """Ban a user"""
    username = request.form.get('username')
    reason = request.form.get('reason', 'No reason provided')
    
    user = User.query.filter_by(username=username).first()
    if not user:
        flash(f'User "{username}" not found!', 'error')
        return redirect(url_for('admin_panel'))
    
    if user.is_admin:
        flash('Cannot ban an admin user!', 'error')
        return redirect(url_for('admin_panel'))
    
    if user.is_banned:
        flash(f'User "{username}" is already banned!', 'warning')
        return redirect(url_for('admin_panel'))
    
    # Ban user
    user.is_banned = True
    db.session.commit()
    
    # Log ban action
    ban_log = BanLog(
        username=username,
        action='ban',
        admin_username=current_user.username,
        reason=reason
    )
    db.session.add(ban_log)
    db.session.commit()
    
    flash(f'User "{username}" has been BANNED!', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/unban-user', methods=['POST'])
@login_required
@admin_required
def admin_unban_user():
    """Unban a user"""
    username = request.form.get('username')
    reason = request.form.get('reason', 'No reason provided')
    
    user = User.query.filter_by(username=username).first()
    if not user:
        flash(f'User "{username}" not found!', 'error')
        return redirect(url_for('admin_panel'))
    
    if not user.is_banned:
        flash(f'User "{username}" is not banned!', 'warning')
        return redirect(url_for('admin_panel'))
    
    # Unban user
    user.is_banned = False
    db.session.commit()
    
    # Log unban action
    ban_log = BanLog(
        username=username,
        action='unban',
        admin_username=current_user.username,
        reason=reason
    )
    db.session.add(ban_log)
    db.session.commit()
    
    flash(f'User "{username}" has been UNBANNED!', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/update-banner', methods=['POST'])
@login_required
@admin_required
def admin_update_banner():
    """Update banner image"""
    banner_url = request.form.get('banner_url', '').strip()
    
    if not banner_url:
        flash('Please enter a valid image URL!', 'error')
        return redirect(url_for('admin_panel'))
    
    banner = Banner.query.first()
    if banner:
        banner.image_url = banner_url
        banner.updated_at = datetime.utcnow()
        banner.updated_by = current_user.username
    else:
        banner = Banner(
            image_url=banner_url,
            updated_by=current_user.username
        )
        db.session.add(banner)
    
    db.session.commit()
    flash('Banner updated successfully!', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/delete-user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_user(user_id):
    """Delete a user (admin only)"""
    user = User.query.get_or_404(user_id)
    
    if user.is_admin:
        flash('Cannot delete admin user!', 'error')
        return redirect(url_for('admin_panel'))
    
    if user.is_banned:
        flash('Cannot delete banned user! Please unban first.', 'error')
        return redirect(url_for('admin_panel'))
    
    # Delete user's files
    for file in user.files:
        if os.path.exists(file.file_path):
            os.remove(file.file_path)
        db.session.delete(file)
    
    # Delete user
    username = user.username
    db.session.delete(user)
    db.session.commit()
    
    flash(f'User "{username}" deleted successfully!', 'success')
    return redirect(url_for('admin_panel'))