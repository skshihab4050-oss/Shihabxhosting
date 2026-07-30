import os

class Config:
    SECRET_KEY = 'shihab-x-hosting-secret-key-2026'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///../database.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = '../uploads'
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB max file size
    ALLOWED_EXTENSIONS = {'py', 'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'zip', 'rar', 'html', 'css', 'js'}

# Create upload folder if it doesn't exist
os.makedirs('../uploads', exist_ok=True)