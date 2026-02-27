#!/usr/bin/env python
import os
from app import app, db
from models import User


@app.cli.command('init-db')
def init_db():
    """Initialize the database"""
    db.create_all()
    print('Database initialized.')


@app.cli.command('create-admin')
def create_admin():
    """Create admin user"""
    from getpass import getpass

    username = input('Admin username: ')
    email = input('Admin email: ')
    password = getpass('Admin password: ')

    admin = User(
        username=username,
        email=email,
        display_name='Administrator',
        is_admin=True,
        is_verified=True
    )
    admin.password = password

    db.session.add(admin)
    db.session.commit()

    print(f'Admin user {username} created.')


if __name__ == '__main__':
    app.run(debug=True)
