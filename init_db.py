# init_db.py
from app import app, db
from models import User, SocialLink, GalleryImage, Post, Comment, Follow, VerificationRequest, Notification

with app.app_context():
    # Create all tables
    db.create_all()
    print("✅ Database tables created successfully!")

    # Check if admin user exists, if not create one
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@velvetsignals.com',
            display_name='Administrator',
            is_admin=True,
            is_verified=True,
            is_active=True
        )
        admin.password = 'Admin123!'  # This will be hashed automatically
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin user created - Username: admin, Password: Admin123!")
    else:
        print("✅ Admin user already exists")
