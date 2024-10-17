from flask import Flask, render_template, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.utils import secure_filename
import uuid
import datetime

# Initialize Flask application
app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost:3306/ppflask'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Import routes
from routes.user import *  # Import everything from user.py
from routes.category import *  # Import everything from category.py


@app.route('/')
def hello_world():
    return render_template('admin/index.html')


@app.route('/admin/user')
def user():
    return render_template('admin/user.html')


@app.route('/admin/category')
def category():
    return render_template('admin/category.html')


@app.route('/admin/product')
def product():
    return render_template('admin/product.html')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create tables if they don't exist
        app.run(debug=True)
