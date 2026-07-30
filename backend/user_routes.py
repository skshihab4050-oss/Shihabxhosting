from flask import request, redirect, url_for, flash, jsonify, session
from flask_login import login_required, current_user
from datetime import datetime
import os

from backend.app import app, db
from backend.models import User, File
from backend.auth import user_required

# ========== USER PROFILE ==========

@app.route('/profile')
@login_required
@user_required
def user_profile():
    """User profile page"""
    return render_template('profile.html', user=current_user)

@app.route('/api/user/profile')
@login_required
@user_required
def api_user_profile():
    """Get user profile (API)"""
    return jsonify({
        'success': True,
        'user': current_user.to_dict()
    })

@app.route('/api/user/update', methods=['POST'])
@login_required
@user_required
def api_user_update():
    """Update user profile (API)"""
    data = request.get_json()
    
    email = data.get('email', '').strip()
    
    if email and email != current_user.email:
        if User.query.filter_by(email=email).first():
            return jsonify({'success': False, 'message': 'Email already registered!'})
        current_user.email = email
    
    db.session.commit()
    return jsonify({
        'success': True,
        'message': 'Profile updated successfully!',
        'user': current_user.to_dict()
    })

@app.route('/api/user/change-password', methods=['POST'])
@login_required
@user_required
def api_user_change_password():
    """Change user password (API)"""
    from werkzeug.security import generate_password_hash, check_password_hash
    
    data = request.get_json()
    old_password = data.get('old_password', '').strip()
    new_password = data.get('new_password', '').strip()
    
    if not check_password_hash(current_user.password, old_password):
        return jsonify({'success': False, 'message': 'Current password is incorrect!'})
    
    if len(new_password) < 4:
        return jsonify({'success': False, 'message': 'New password must be at least 4 characters!'})
    
    current_user.password = generate_password_hash(new_password)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Password changed successfully!'})

# ========== USER FILES (API) ==========

@app.route('/api/files')
@login_required
@user_required
def api_get_files():
    """Get user files (API)"""
    files = File.query.filter_by(user_id=current_user.id).order_by(File.uploaded_at.desc()).all()
    return jsonify({
        'success': True,
        'files': [file.to_dict() for file in files]
    })

@app.route('/api/upload', methods=['POST'])
@login_required
@user_required
def api_upload_file():
    """Upload file (API)"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file uploaded!'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected!'})
    
    from werkzeug.utils import secure_filename
    from backend.config import Config
    
    # Check file extension
    allowed_extensions = {'py', 'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'zip', 'rar', 'html', 'css', 'js', 'json', 'xml', 'csv'}
    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    
    if ext not in allowed_extensions:
        return jsonify({'success': False, 'message': f'File type .{ext} is not allowed!'})
    
    # Save file
    original_filename = file.filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    secure_name = secure_filename(f"{timestamp}_{original_filename}")
    file_path = os.path.join(Config.UPLOAD_FOLDER, secure_name)
    file.save(file_path)
    
    file_size = os.path.getsize(file_path)
    
    new_file = File(
        filename=secure_name,
        original_filename=original_filename,
        file_path=file_path,
        file_size=file_size,
        file_type=ext if ext else 'unknown',
        user_id=current_user.id
    )
    db.session.add(new_file)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'File uploaded successfully!',
        'file': new_file.to_dict()
    })

@app.route('/api/files/<int:file_id>', methods=['DELETE'])
@login_required
@user_required
def api_delete_file(file_id):
    """Delete file (API)"""
    file = File.query.get_or_404(file_id)
    
    if file.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Access denied!'})
    
    if os.path.exists(file.file_path):
        os.remove(file.file_path)
    
    db.session.delete(file)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'File deleted successfully!'})

# ========== USER DASHBOARD STATS ==========

@app.route('/api/dashboard/stats')
@login_required
@user_required
def api_dashboard_stats():
    """Get dashboard statistics (API)"""
    file_count = File.query.filter_by(user_id=current_user.id).count()
    total_size = db.session.query(db.func.sum(File.file_size)).filter_by(user_id=current_user.id).scalar() or 0
    
    return jsonify({
        'success': True,
        'stats': {
            'file_count': file_count,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'ram': current_user.ram,
            'cpu': current_user.cpu
        }
    })

# ========== USER ACTIVITY ==========

@app.route('/api/user/activity')
@login_required
@user_required
def api_user_activity():
    """Get user activity (API)"""
    # Get last 10 uploaded files
    recent_files = File.query.filter_by(user_id=current_user.id).order_by(File.uploaded_at.desc()).limit(10).all()
    
    return jsonify({
        'success': True,
        'recent_files': [file.to_dict() for file in recent_files]
    })

# ========== USER BAN STATUS ==========

@app.route('/api/user/ban-status')
@login_required
def api_ban_status():
    """Check user ban status (API)"""
    return jsonify({
        'success': True,
        'is_banned': current_user.is_banned,
        'message': 'Account is banned!' if current_user.is_banned else 'Account is active'
    })