from flask import request, jsonify
from app import app
from sqlalchemy import create_engine, text
import os
from werkzeug.utils import secure_filename
import uuid
import datetime

# Configuration
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'static', 'admin', 'assets', 'images', 'main_img')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit file size to 16 MB

# Allowed extensions for main_img pictures
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Create a database engine
engine = create_engine("mysql+mysqlconnector://root:@127.0.0.1/ppflask")

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
                'profile_pic': item[7]
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

    # Validate required fields
    if not username or not email:
        return jsonify({'error': 'Username and Email are required fields.'}), 400

    query = text("""
        INSERT INTO `users` (username, gender, phone, email, role, address, profile_pic)
        VALUES (:username, :gender, :phone, :email, :role, :address, :profile_pic)
    """)

    with engine.connect() as connection:
        result = connection.execute(query, {
            'username': username,
            'gender': gender,
            'phone': phone,
            'email': email,
            'role': role,
            'address': address,
            'profile_pic': profile_pic_filename
        })
        connection.commit()

        # Fetch the newly created user
        new_user_id = result.lastrowid
        new_user = connection.execute(text("SELECT * FROM users WHERE id = :id"), {'id': new_user_id}).fetchone()

    return jsonify(dict(new_user._mapping)), 201

@app.route('/api/users/<int:user_id>', methods=['PUT'])
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

    # Validate required fields
    if not username or not email:
        return jsonify({'error': 'Username and Email are required fields.'}), 400

    query = text("""
        UPDATE `users`
        SET username = :username, gender = :gender, phone = :phone, email = :email, role = :role, address = :address, profile_pic = :profile_pic
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
            'user_id': user_id
        })
        connection.commit()

        # Fetch the updated user
        updated_user = connection.execute(text("SELECT * FROM users WHERE id = :id"), {'id': user_id}).fetchone()

    return jsonify(dict(updated_user._mapping)), 200

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
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

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    ext = file.filename.rsplit('.', 1)[1].lower()
    unique_filename = f"{timestamp}_{uuid.uuid4().hex}.{ext}"
    filename = secure_filename(unique_filename)

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)

    return filename
