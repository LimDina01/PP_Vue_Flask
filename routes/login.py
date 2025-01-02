from flask import request, jsonify, session, redirect
from app import app
from sqlalchemy import create_engine, text
import os
from werkzeug.utils import secure_filename
import uuid
import datetime
from PIL import Image
import bcrypt  # Import bcrypt for password hashing
from flask import Flask, session

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set a secret key for session management
# Configuration
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'static', 'admin', 'assets', 'images', 'main_img')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit file size to 16 MB

# Allowed extensions for main_img pictures
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Create a database engine
engine = create_engine("mysql+mysqlconnector://root:@127.0.0.1/ppflask")
