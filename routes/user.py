from flask import render_template, request, jsonify
from app import app, db  # Import db from app
import os
from werkzeug.utils import secure_filename
import uuid
import datetime

# Configuration
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'static', 'admin', 'assets', 'images', 'profile')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit file size to 16 MB

# Allowed extensions for profile pictures
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    gender = db.Column(db.String(10))
    role = db.Column(db.String(20))
    phone = db.Column(db.String(15))
    email = db.Column(db.String(120), nullable=False, unique=True)
    address = db.Column(db.String(255))
    profile_pic = db.Column(db.String(255), default='default.png')  # Store only the filename


@app.route('/api/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([{
        'id': user.id,
        'username': user.username,
        'gender': user.gender,
        'role': user.role,
        'phone': user.phone,
        'email': user.email,
        'address': user.address,
        'profile_pic': user.profile_pic
    } for user in users])


@app.route('/api/users', methods=['POST'])
def add_user():
    data = request.form
    username = data.get('username')
    gender = data.get('gender')
    role = data.get('role')
    phone = data.get('phone')
    email = data.get('email')
    address = data.get('address')

    # Validate required fields
    if not username or not email:
        return jsonify({'error': 'Username and Email are required fields.'}), 400

    # Check if email already exists
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already exists.'}), 400

    # Handle profile picture
    profile_pic = request.files.get('profilePic')
    profile_pic_filename = 'default.png'  # Default profile picture

    if profile_pic and allowed_file(profile_pic.filename):
        profile_pic_filename = save_profile_pic(profile_pic)
    elif profile_pic:
        return jsonify({'error': 'Invalid file type for profile picture.'}), 400

    # Create the new user instance
    new_user = User(
        username=username,
        gender=gender,
        role=role,
        phone=phone,
        email=email,
        address=address,
        profile_pic=profile_pic_filename  # Store only the filename
    )

    try:
        db.session.add(new_user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to add user.', 'details': str(e)}), 500

    return jsonify({
        'id': new_user.id,
        'username': new_user.username,
        'gender': new_user.gender,
        'role': new_user.role,
        'phone': new_user.phone,
        'email': new_user.email,
        'address': new_user.address,
        'profile_pic': new_user.profile_pic,
        'message': 'User added successfully!'
    }), 201


@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found.'}), 404

    data = request.form
    username = data.get('username')
    gender = data.get('gender')
    role = data.get('role')
    phone = data.get('phone')
    email = data.get('email')
    address = data.get('address')

    # Validate required fields
    if not username or not email:
        return jsonify({'error': 'Username and Email are required fields.'}), 400

    # Check if email is being updated to an existing email
    existing_user = User.query.filter_by(email=email).first()
    if existing_user and existing_user.id != user.id:
        return jsonify({'error': 'Email already exists.'}), 400

    # Update fields
    user.username = username
    user.gender = gender
    user.role = role
    user.phone = phone
    user.email = email
    user.address = address

    # Handle profile picture
    profile_pic = request.files.get('profilePic')
    if profile_pic:
        if allowed_file(profile_pic.filename):
            # Delete old profile picture if it's not the default
            if user.profile_pic and user.profile_pic != 'default.png':
                delete_profile_pic(user.profile_pic)
            # Save new profile picture
            user.profile_pic = save_profile_pic(profile_pic)
        else:
            return jsonify({'error': 'Invalid file type for profile picture.'}), 400

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update user.', 'details': str(e)}), 500

    return jsonify({
        'id': user.id,
        'username': user.username,
        'gender': user.gender,
        'role': user.role,
        'phone': user.phone,
        'email': user.email,
        'address': user.address,
        'profile_pic': user.profile_pic,
        'message': 'User updated successfully!'
    }), 200


@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found.'}), 404

    try:
        # Delete profile picture if it's not the default
        if user.profile_pic and user.profile_pic != 'default.png':
            delete_profile_pic(user.profile_pic)

        db.session.delete(user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete user.', 'details': str(e)}), 500

    return jsonify({'message': 'User deleted successfully!'}), 200


def allowed_file(filename):
    """Check if the file has an allowed extension."""
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_profile_pic(file):
    """Save the uploaded profile picture and return the filename."""
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    # Get the current date and time formatted as YYYYMMDD_HHMMSS
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    # Get the file extension
    ext = file.filename.rsplit('.', 1)[1].lower()

    # Generate a unique filename using the timestamp and original filename
    unique_filename = f"{timestamp}_{uuid.uuid4().hex}.{ext}"
    filename = secure_filename(unique_filename)

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    return filename  # Return only the filename


def delete_profile_pic(filename):
    """Delete a profile picture file from the upload folder."""
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        os.remove(file_path)
