from flask import Flask, render_template, request, jsonify, abort, url_for, redirect
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.utils import secure_filename
import uuid
import datetime
from functools import wraps

# Initialize Flask application
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a random secret key

# Set the SameSite attribute for session cookies
app.config['SESSION_COOKIE_SAMESITE'] = 'None'  # or 'Lax' based on your needs
app.config['SESSION_COOKIE_SECURE'] = True  # Ensure cookies are sent over HTTPS

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost:3306/ppflask'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Import routes
from routes.user import *  # Import everything from user.py
from routes.category import *  # Import everything from category.py

def login_required(f):
    """Decorator to check if the user is logged in."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login_page'))  # Redirect to login page
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin')
@login_required
@admin_required
def hello_world():  
    return render_template('admin/index.html')


@app.route('/admin/user')
@login_required
@admin_required
def user():
    return render_template('admin/user.html')


@app.route('/admin/category')
@login_required
@admin_required
def category():
    return render_template('admin/category.html')


@app.route('/admin/product')
@login_required
@admin_required
def product():
    return render_template('admin/product.html')


@app.route('/admin/sale')
@login_required
@admin_required
def sale():
    return render_template('admin/sale.html')

# =========================================================

@app.route('/customer/index')
@login_required
def customer():
    return render_template('customer/index.html')

# =========================================================

@app.route('/login')
def login_page():
    return render_template('login/login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect("/login")
    # return jsonify({'message': 'Logged out successfully!'}), 200

@app.route('/')
def default():
    return redirect(url_for('customer'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create tables if they don't exist
        app.run(debug=True)
