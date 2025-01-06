from flask import request, jsonify, session, redirect, url_for
from app import app
from sqlalchemy import create_engine, text
import os
from werkzeug.utils import secure_filename
import uuid
import datetime
from PIL import Image
import bcrypt  # Import bcrypt for password hashing
from functools import wraps  # Import wraps to preserve function metadata
from sqlalchemy.engine import Row  # Import Row for named access

# Configuration
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'static', 'admin', 'assets', 'images', 'main_img')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit file size to 16 MB

# Allowed extensions for main_img pictures
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Create a database engine
engine = create_engine("mysql+mysqlconnector://root:@127.0.0.1/ppflask")

def admin_required(f):
    """Decorator to check if the user is an admin."""
    @wraps(f)  # Preserve the original function's metadata
    def wrapper(*args, **kwargs):
        if 'user_id' not in session or not is_admin(session['user_id']):
            
            return jsonify({'error': 'Access denied. Admins only.'}), 403
        return f(*args, **kwargs)
    return wrapper



def is_admin(user_id):
    """Check if the user is an admin based on their role."""
    with engine.connect() as connection:
        result = connection.execute(text("SELECT role FROM users WHERE id = :id"), {'id': user_id}).fetchone()
        return result is not None and result[0] == 'Admin'  # Access by index

@app.route('/api/users', methods=['GET'])
def get_users():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT * FROM users"))
        data = result.fetchall()
        user_list = [
            {
                'id': item[0],
                'username': item[1],
                'gender': item[2],
                'role': item[3],
                'phone': item[4],
                'email': item[5],
                'address': item[6],
                'profile_pic': item[7],
                # Do not return the password for security reasons
            }
            for item in data
        ]
    return jsonify(user_list)

@app.route('/api/users', methods=['POST'])
def add_user():
    # Check if the request contains the file part
    if 'profilePic' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['profilePic']
    if file and allowed_file(file.filename):
        profile_pic_filename = save_profile_pic(file)
    else:
        profile_pic_filename = 'default.png'

    # Extract other form data
    username = request.form.get('username')
    gender = request.form.get('gender')
    role = request.form.get('role')
    phone = request.form.get('phone')
    email = request.form.get('email')
    address = request.form.get('address')
    password = request.form.get('password')

    # Validate required fields
    if not username or not email:
        return jsonify({'error': 'Username and Email are required fields.'}), 400
    if not password:
        return jsonify({'error': 'Password required fields.'}), 400
    if not role:
        return jsonify({'error': 'Role required fields.'}), 400

    # Hash the password using bcrypt
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    query = text("""
        INSERT INTO `users` (username, gender, phone, email, role, address, profile_pic, password)
        VALUES (:username, :gender, :phone, :email, :role, :address, :profile_pic, :password)
    """)

    with engine.connect() as connection:
        result = connection.execute(query, {
            'username': username,
            'gender': gender,
            'phone': phone,
            'email': email,
            'role': role,
            'address': address,
            'profile_pic': profile_pic_filename,
            'password': hashed_password  # Store the hashed password
        })
        connection.commit()

        # Fetch the newly created user
        new_user_id = result.lastrowid
        new_user = connection.execute(text("SELECT * FROM users WHERE id = :id"), {'id': new_user_id}).fetchone()

    return jsonify(dict(new_user._mapping)), 201

@app.route('/api/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    # Check if the request contains the file part
    file = request.files.get('profilePic')
    if file and allowed_file(file.filename):
        profile_pic_filename = save_profile_pic(file)
    else:
        # Fetch the current profile picture from the database if no new file is uploaded
        with engine.connect() as connection:
            current_user = connection.execute(text("SELECT profile_pic FROM users WHERE id = :id"), {'id': user_id}).fetchone()
            profile_pic_filename = current_user._mapping['profile_pic'] if current_user else 'default.png'

    # Extract other form data
    username = request.form.get('username')
    gender = request.form.get('gender')
    role = request.form.get('role')
    phone = request.form.get('phone')
    email = request.form.get('email')
    address = request.form.get('address')
    password = request.form.get('password')

    # Validate required fields
    if not username or not email:
        return jsonify({'error': 'Username and Email are required fields.'}), 400
    if not password:
        return jsonify({'error': 'Password required fields.'}), 400
    if not role:
        return jsonify({'error': 'Role required fields.'}), 400

    # Hash the password if it is provided
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    query = text("""
        UPDATE `users`
        SET username = :username, gender = :gender, phone = :phone, email = :email, role = :role, address = :address, profile_pic = :profile_pic, password = :password
        WHERE id = :user_id
    """)

    with engine.connect() as connection:
        connection.execute(query, {
            'username': username,
            'gender': gender,
            'phone': phone,
            'email': email,
            'role': role,
            'address': address,
            'profile_pic': profile_pic_filename,
            'password': hashed_password,  # Store the hashed password
            'user_id': user_id
        })
        connection.commit()

        # Fetch the updated user
        updated_user = connection.execute(text("SELECT * FROM users WHERE id = :id"), {'id': user_id}).fetchone()

    return jsonify(dict(updated_user._mapping)), 200

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    query = text("DELETE FROM `users` WHERE `id` = :user_id")

    with engine.connect() as connection:
        connection.execute(query, {"user_id": user_id})
        connection.commit()

    return jsonify({"message": "User deleted successfully!"}), 200

def allowed_file(filename):
    """Check if the file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_profile_pic(file):
    """Save the uploaded image and return the filename."""
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    sub_img_folder = os.path.join(os.getcwd(), 'static', 'admin', 'assets', 'images', 'sub_img')
    if not os.path.exists(sub_img_folder):
        os.makedirs(sub_img_folder)

    # Generate unique filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    original_filename = secure_filename(file.filename)
    ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'jpg'
    unique_filename = f"{timestamp}_{uuid.uuid4().hex}.{ext}"

    # Save main image
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    file.save(file_path)

    # Create thumbnail for sub_img
    with Image.open(file_path) as img:
        # Save thumbnail
        sub_img_path = os.path.join(sub_img_folder, unique_filename)
        # Create a copy before saving to avoid potential closed file issues
        img_copy = img.copy()
        img_copy.thumbnail((100, 100))  # Adjust size as needed
        img_copy.save(sub_img_path, optimize=True, quality=70)

    return unique_filename

@app.route('/api/login', methods=['POST'])
def login():
    username_or_email = request.form.get('username')
    password = request.form.get('password')

    # Validate inputs
    if not username_or_email or not password:
        return jsonify({'error': 'Username/Email and Password are required!'}), 400

    query = text("SELECT * FROM `users` WHERE `username` = :username_or_email OR `email` = :username_or_email")
    with engine.connect() as connection:
        user = connection.execute(query, {'username_or_email': username_or_email}).fetchone()

    # Check if user exists
    if user is None:
        return jsonify({'error': 'Invalid credentials!'}), 401

    # Verify password
    user_password = user[8]  # Assuming the password is at index 3
    if not bcrypt.checkpw(password.encode('utf-8'), user_password.encode('utf-8')):
        return jsonify({'error': 'Invalid credentials!'}), 401

    # Create session
    session['user_id'] = user[0]  # Assuming the first index is user ID
    session['username'] = user[1]  # Assuming the second index is username
    

    # Respond with success
    return jsonify({'message': 'Login successful!'}), 200

@app.route('/api/current_user', methods=['GET'])
def current_user():
    if 'user_id' not in session:
        return jsonify({'error': 'User not logged in'}), 401

    # Log session information for debugging
    print(f"Current user: user_id={session['user_id']}, username={session['username']}")

    return jsonify({
        'id': session['user_id'],
        'username': session['username']
    }), 200