from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, PasswordField, BooleanField, TextAreaField, SelectField, DateField, URLField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Optional, URL
import re


def password_complexity(form, field):
    """Custom validator for password complexity"""
    password = field.data
    if len(password) < 8:
        raise ValidationError('Password must be at least 8 characters long')
    if not re.search(r'[A-Z]', password):
        raise ValidationError(
            'Password must contain at least one uppercase letter')
    if not re.search(r'[a-z]', password):
        raise ValidationError(
            'Password must contain at least one lowercase letter')
    if not re.search(r'[0-9]', password):
        raise ValidationError('Password must contain at least one number')
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        raise ValidationError(
            'Password must contain at least one special character')


def username_validator(form, field):
    """Custom validator for username"""
    username = field.data
    if not re.match(r'^[a-zA-Z0-9_]{3,30}$', username):
        raise ValidationError(
            'Username must be 3-30 characters and contain only letters, numbers, and underscores')


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[
                           DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[
                           DataRequired(), Length(min=3, max=80), username_validator])
    email = StringField('Email', validators=[
                        DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Password', validators=[
                             DataRequired(), password_complexity])
    password2 = PasswordField('Confirm Password', validators=[
                              DataRequired(), EqualTo('password', message='Passwords must match')])
    agree_terms = BooleanField(
        'I agree to the Terms of Service and confirm I am 18+', validators=[DataRequired()])


class ProfileForm(FlaskForm):
    display_name = StringField('Display Name', validators=[Length(max=100)])
    bio = TextAreaField('Bio', validators=[Length(max=500)])
    location = StringField('Location', validators=[Length(max=100)])
    website = URLField('Website', validators=[Optional(), URL()])
    birth_date = DateField('Birth Date', validators=[Optional()])


class SocialLinkForm(FlaskForm):
    platform = SelectField('Platform', choices=[
        ('twitter', 'Twitter/X'),
        ('instagram', 'Instagram'),
        ('onlyfans', 'OnlyFans'),
        ('fansly', 'Fansly'),
        ('tiktok', 'TikTok'),
        ('youtube', 'YouTube'),
        ('telegram', 'Telegram'),
        ('discord', 'Discord'),
        ('snapchat', 'Snapchat'),
        ('twitch', 'Twitch'),
        ('allaccessfans', 'AllAccessFans'),
        ('other', 'Other')
    ])
    url = URLField('URL', validators=[DataRequired(), URL()])
    handle = StringField('Handle/Username', validators=[Length(max=100)])


class AvatarUploadForm(FlaskForm):
    avatar = FileField('Profile Picture', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 'Images only!')
    ])


class WallpaperUploadForm(FlaskForm):
    wallpaper = FileField('Cover Image', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 'Images only!')
    ])


class GalleryImageForm(FlaskForm):
    image = FileField('Image', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 'Images only!')
    ])
    caption = StringField('Caption', validators=[Length(max=200)])


class PostForm(FlaskForm):
    content = TextAreaField('What\'s on your mind?', validators=[
                            DataRequired(), Length(max=1000)])
    media = FileField('Media (optional)', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp',
                    'mp4', 'mov'], 'Images and videos only!')
    ])


class SearchForm(FlaskForm):
    query = StringField('Search', validators=[
                        DataRequired(), Length(min=2, max=100)])


class ContactForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    subject = StringField('Subject', validators=[
                          DataRequired(), Length(max=200)])
    message = TextAreaField('Message', validators=[
                            DataRequired(), Length(max=5000)])


class VerificationRequestForm(FlaskForm):
    id_proof = FileField('ID Document', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'jpeg', 'png', 'pdf'], 'Images and PDFs only!')
    ])
    selfie = FileField('Selfie with ID', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')
    ])
    notes = TextAreaField('Additional Notes', validators=[Length(max=500)])


class AdminUserEditForm(FlaskForm):
    username = StringField('Username', validators=[
                           DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    display_name = StringField('Display Name', validators=[Length(max=100)])
    is_verified = BooleanField('Verified')
    is_featured = BooleanField('Featured')
    is_admin = BooleanField('Admin')
    is_active = BooleanField('Active')


class VerificationRequestForm(FlaskForm):
    id_proof = FileField('ID Document', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'jpeg', 'png', 'pdf'], 'Images and PDFs only!')
    ])
    selfie = FileField('Selfie with ID', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')
    ])
    notes = TextAreaField('Additional Notes', validators=[Length(max=500)])
