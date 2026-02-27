# update_db.py
from app import app, db
from models import User
from sqlalchemy import inspect, text


def update_database():
    with app.app_context():
        # Create tables if they don't exist (won't modify existing ones)
        db.create_all()
        print("✅ Base tables verified")

        # Check what columns currently exist
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('users')]
        print(f"Current columns in users table: {columns}")

        # Add missing columns one by one
        if 'is_approved' not in columns:
            print("Adding is_approved column...")
            db.session.execute(
                text('ALTER TABLE users ADD COLUMN is_approved BOOLEAN DEFAULT 0'))
            print("✅ Added is_approved")

        if 'is_flagged' not in columns:
            print("Adding is_flagged column...")
            db.session.execute(
                text('ALTER TABLE users ADD COLUMN is_flagged BOOLEAN DEFAULT 0'))
            print("✅ Added is_flagged")

        if 'is_rejected' not in columns:
            print("Adding is_rejected column...")
            db.session.execute(
                text('ALTER TABLE users ADD COLUMN is_rejected BOOLEAN DEFAULT 0'))
            print("✅ Added is_rejected")

        # Commit the changes
        db.session.commit()

        # Verify columns were added
        inspector = inspect(db.engine)
        updated_columns = [col['name']
                           for col in inspector.get_columns('users')]
        print(f"Updated columns: {updated_columns}")

        # Set default values for existing users
        db.session.execute(
            text('UPDATE users SET is_approved = 1 WHERE is_approved IS NULL'))
        db.session.execute(
            text('UPDATE users SET is_flagged = 0 WHERE is_flagged IS NULL'))
        db.session.execute(
            text('UPDATE users SET is_rejected = 0 WHERE is_rejected IS NULL'))
        db.session.commit()
        print("✅ Set default values for existing users")

        print("\n🎉 Database update complete!")


if __name__ == '__main__':
    update_database()
