from flask import request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime
import os

from backend.app import app, db
from backend.models import User, File, Banner, BanLog
from backend.auth import admin_required
from backend.config import Config

# ========== ADMIN USER MANAGEMENT ==========

@app.route('/admin/users')
@login_required
@admin_required
def admin_get_users():
    """Get all users (API)"""
    users = User.query.order_by(User.created_at.desc()).all()
    return jsonify({
        'success': True,
        'users': [user.to_dict() for user in users]
    })

@app.route('/admin/user/<int:user_id>')
@login_required
@admin_required
def admin_get_user(user_id):
    """Get single user details"""
    user = User.query.get_or_404(user_id)
    return jsonify({
        'success': True,
        'user': user.to_dict()
    })

@app.route('/admin/update-user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def admin_update_user(user_id):
    """Update user details"""
    user = User.query.get_or_404(user_id)
    
    if user.is_admin and current_user.id != user.id:
        flash('Cannot modify another admin user!', 'error')
        return redirect(url_for('admin_panel'))
    
    username = request.form.get('username')
    email = request.form.get('email')
    ram = int(request.form.get('ram', 20))
    cpu = int(request.form.get('cpu', 100))
    
    # Check username conflict
    if username and username != user.username:
        if User.query.filter_by(username=username).first():
            flash('Username already taken!', 'error')
            return redirect(url_for('admin_panel'))
        user.username = username
    
    if email and email != user.email:
        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'error')
            return redirect(url_for('admin_panel'))
        user.email = email
    
    user.ram = ram
    user.cpu = cpu
    
    db.session.commit()
    flash(f'User "{user.username}" updated successfully!', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/change-password', methods=['POST'])
@login_required
@admin_required
def admin_change_password():
    """Change user password"""
    username = request.form.get('username')
    new_password = request.form.get('new_password')
    
    user = User.query.filter_by(username=username).first()
    if not user:
        flash('User not found!', 'error')
        return redirect(url_for('admin_panel'))
    
    if len(new_password) < 4:
        flash('Password must be at least 4 characters!', 'error')
        return redirect(url_for('admin_panel'))
    
    from werkzeug.security import generate_password_hash
    user.password = generate_password_hash(new_password)
    db.session.commit()
    
    flash(f'Password changed for "{username}"!', 'success')
    return redirect(url_for('admin_panel'))

# ========== ADMIN FILE MANAGEMENT ==========

@app.route('/admin/files')
@login_required
@admin_required
def admin_get_files():
    """Get all files (API)"""
    files = File.query.order_by(File.uploaded_at.desc()).all()
    return jsonify({
        'success': True,
        'files': [file.to_dict() for file in files]
    })

@app.route('/admin/delete-all-files/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_all_files(user_id):
    """Delete all files of a user"""
    user = User.query.get_or_404(user_id)
    
    for file in user.files:
        if os.path.exists(file.file_path):
            os.remove(file.file_path)
        db.session.delete(file)
    
    db.session.commit()
    flash(f'All files of "{user.username}" deleted!', 'success')
    return redirect(url_for('admin_panel'))

# ========== ADMIN BAN LOGS ==========

@app.route('/admin/ban-logs')
@login_required
@admin_required
def admin_ban_logs():
    """View ban logs"""
    logs = BanLog.query.order_by(BanLog.created_at.desc()).limit(50).all()
    return render_template('admin-ban-logs.html', logs=logs)

@app.route('/admin/ban-logs-api')
@login_required
@admin_required
def admin_ban_logs_api():
    """Get ban logs as JSON"""
    logs = BanLog.query.order_by(BanLog.created_at.desc()).limit(100).all()
    return jsonify({
        'success': True,
        'logs': [log.to_dict() for log in logs]
    })

# ========== ADMIN STATS ==========

@app.route('/admin/stats')
@login_required
@admin_required
def admin_stats():
    """Get admin statistics (API)"""
    total_users = User.query.count()
    banned_users = User.query.filter_by(is_banned=True).count()
    total_files = File.query.count()
    total_size = db.session.query(db.func.sum(File.file_size)).scalar() or 0
    
    # Get recent users
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    return jsonify({
        'success': True,
        'stats': {
            'total_users': total_users,
            'banned_users': banned_users,
            'total_files': total_files,
            'total_size_mb': round(total_size / (1024 * 1024), 2)
        },
        'recent_users': [user.to_dict() for user in recent_users]
    })

# ========== ADMIN SYSTEM ==========

@app.route('/admin/clear-cache', methods=['POST'])
@login_required
@admin_required
def admin_clear_cache():
    """Clear system cache (placeholder)"""
    flash('Cache cleared successfully!', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/system-info')
@login_required
@admin_required
def admin_system_info():
    """Get system information"""
    import platform
    import psutil
    
    return jsonify({
        'success': True,
        'system': {
            'os': platform.system(),
            'os_version': platform.version(),
            'python_version': platform.python_version(),
            'cpu_count': psutil.cpu_count(),
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory': {
                'total_gb': round(psutil.virtual_memory().total / (1024**3), 2),
                'available_gb': round(psutil.virtual_memory().available / (1024**3), 2),
                'percent': psutil.virtual_memory().percent
            },
            'disk': {
                'total_gb': round(psutil.disk_usage('/').total / (1024**3), 2),
                'used_gb': round(psutil.disk_usage('/').used / (1024**3), 2),
                'free_gb': round(psutil.disk_usage('/').free / (1024**3), 2),
                'percent': psutil.disk_usage('/').percent
            }
        }
    })