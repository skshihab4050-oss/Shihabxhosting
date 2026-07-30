from flask import Flask
from flask_login import LoginManager
import os

from backend.config import Config
from backend.models import db, User, Banner

# Initialize Flask app
app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.config.from_object(Config)

# Initialize database
db.init_app(app)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Import routes
from backend import auth, routes, admin_routes, user_routes

# Create tables and default data
def create_default_data():
    with app.app_context():
        db.create_all()
        
        # Create admin if not exists
        from werkzeug.security import generate_password_hash
        admin = User.query.filter_by(username='shihab').first()
        if not admin:
            admin = User(
                username='shihab',
                password=generate_password_hash('shihab123'),
                email='admin@shihab.com',
                ram=20,
                cpu=100,
                is_admin=True,
                is_banned=False
            )
            db.session.add(admin)
            db.session.commit()
            print('✅ Admin user created: shihab / shihab123')
        
        # Create default banner if not exists
        banner = Banner.query.first()
        if not banner:
            banner = Banner(
                image_url='/static/images/banner-default.jpg',
                updated_by='system'
            )
            db.session.add(banner)
            db.session.commit()
            print('✅ Default banner created')
        
        # Create upload folder if not exists
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        print('✅ Upload folder created')

# Call on startup
create_default_data()