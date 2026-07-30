from flask import request, redirect, url_for, flash, session, render_template
from flask_login import login_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

from backend.app import app, db
from backend.models import User

# ========== AUTH DECORATORS ==========

def admin_required(f):
    """Decorator to check if user is admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please login first!', 'error')
            return redirect(url_for('admin_login'))
        if not current_user.is_admin:
            flash('Access denied! Admin only.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def user_required(f):
    """Decorator to check if user is authenticated and not banned"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please login first!', 'error')
            return redirect(url_for('login'))
        if current_user.is_banned:
            flash('Your account has been banned!', 'error')
            return redirect(url_for('banned'))
        return f(*args, **kwargs)
    return decorated_function

# ========== AUTH ROUTES ==========

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not username or not password:
            flash('Please enter both username and password!', 'error')
            return render_template('login.html')
        
        user = User.query.filter_by(username=username).first()
        
        if not user:
            flash('Invalid username or password!', 'error')
            return render_template('login.html')
        
        if not check_password_hash(user.password, password):
            flash('Invalid username or password!', 'error')
            return render_template('login.html')
        
        # Check if user is banned
        if user.is_banned:
            flash('Your account has been banned! Please contact admin.', 'error')
            return redirect(url_for('banned'))
        
        # Login user
        login_user(user)
        session['username'] = user.username
        session['user_id'] = user.id
        
        flash(f'Welcome back, {user.username}!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('login.html')

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    """Admin login"""
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin_panel'))
        else:
            flash('Access denied!', 'error')
            return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not username or not password:
            flash('Please enter both username and password!', 'error')
            return render_template('admin-login.html')
        
        user = User.query.filter_by(username=username).first()
        
        if not user:
            flash('Invalid admin credentials!', 'error')
            return render_template('admin-login.html')
        
        if not check_password_hash(user.password, password):
            flash('Invalid admin credentials!', 'error')
            return render_template('admin-login.html')
        
        if not user.is_admin:
            flash('Access denied! You are not an admin.', 'error')
            return render_template('admin-login.html')
        
        if user.is_banned:
            flash('Admin account is banned!', 'error')
            return redirect(url_for('banned'))
        
        # Login admin
        login_user(user)
        session['username'] = user.username
        session['user_id'] = user.id
        session['is_admin'] = True
        
        flash(f'Welcome Admin {user.username}!', 'success')
        return redirect(url_for('admin_panel'))
    
    return render_template('admin-login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        email = request.form.get('email', '').strip()
        
        # Validation
        if not username or not password:
            flash('Username and password are required!', 'error')
            return render_template('register.html')
        
        if len(username) < 3:
            flash('Username must be at least 3 characters!', 'error')
            return render_template('register.html')
        
        if len(password) < 4:
            flash('Password must be at least 4 characters!', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(username=username).first():
            flash(f'Username "{username}" is already taken!', 'error')
            return render_template('register.html')
        
        if email and User.query.filter_by(email=email).first():
            flash(f'Email "{email}" is already registered!', 'error')
            return render_template('register.html')
        
        # Create user
        hashed_password = generate_password_hash(password)
        user = User(
            username=username,
            password=hashed_password,
            email=email if email else None,
            ram=20,  # Default RAM
            cpu=100,  # Default CPU
            is_admin=False,
            is_banned=False
        )
        db.session.add(user)
        db.session.commit()
        
        flash(f'Account created successfully! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

# ========== API AUTH ROUTES (for AJAX) ==========

@app.route('/api/login', methods=['POST'])
def api_login():
    """API login for AJAX requests"""
    import json
    
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    user = User.query.filter_by(username=username).first()
    
    if user and check_password_hash(user.password, password):
        if user.is_banned:
            return json.jsonify({'success': False, 'message': 'Account is banned!'})
        
        login_user(user)
        session['username'] = user.username
        
        return json.jsonify({
            'success': True,
            'token': 'dummy-token-' + str(user.id),
            'user': user.to_dict()
        })
    
    return json.jsonify({'success': False, 'message': 'Invalid credentials!'})

@app.route('/api/admin-login', methods=['POST'])
def api_admin_login():
    """API admin login for AJAX requests"""
    import json
    
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    user = User.query.filter_by(username=username, is_admin=True).first()
    
    if user and check_password_hash(user.password, password):
        if user.is_banned:
            return json.jsonify({'success': False, 'message': 'Admin account is banned!'})
        
        login_user(user)
        session['username'] = user.username
        
        return json.jsonify({
            'success': True,
            'token': 'admin-token-' + str(user.id),
            'user': user.to_dict()
        })
    
    return json.jsonify({'success': False, 'message': 'Invalid admin credentials!'})

@app.route('/api/logout', methods=['POST'])
def api_logout():
    """API logout"""
    logout_user()
    session.clear()
    return {'success': True}