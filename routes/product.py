from flask import Flask, render_template, request, jsonify
from app import app, db  # Import db from app
import os
from werkzeug.utils import secure_filename
import uuid
import datetime

# Configuration
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'static', 'admin', 'assets', 'images', 'product_img')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit file size to 16 MB

# Allowed extensions for product images
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    product_code = db.Column(db.String(50), nullable=False, unique=True)
    product_name = db.Column(db.String(80), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    cost = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    current_stock = db.Column(db.Integer, nullable=False)
    image = db.Column(db.String(255), default='default.png')  # Store only the filename

@app.route('/api/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    return jsonify([{
        'id': product.id,
        'product_code': product.product_code,
        'product_name': product.product_name,
        'category_id': product.category_id,
        'cost': product.cost,
        'price': product.price,
        'current_stock': product.current_stock,
        'image': product.image
    } for product in products])

@app.route('/api/products', methods=['POST'])
def add_product():
    data = request.form
    product_code = data.get('product_code')
    product_name = data.get('product_name')
    category_id = data.get('category_id')
    cost = data.get('cost')
    price = data.get('price')
    current_stock = data.get('current_stock')

    # Validate required fields
    if not product_code or not product_name or not category_id or not cost or not price or not current_stock:
        return jsonify({'error': 'All fields are required.'}), 400

    # Handle product image
    image_file = request.files.get('image')
    image_filename = 'default.png'  # Default product image

    if image_file and allowed_file(image_file.filename):
        image_filename = save_image(image_file)
    elif image_file:
        return jsonify({'error': 'Invalid file type for product image.'}), 400

    # Create the new product instance
    new_product = Product(
        product_code=product_code,
        product_name=product_name,
        category_id=category_id,
        cost=float(cost),
        price=float(price),
        current_stock=int(current_stock),
        image=image_filename  # Store only the filename
    )

    try:
        db.session.add(new_product)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to add product.', 'details': str(e)}), 500

    return jsonify({
        'id': new_product.id,
        'product_code': new_product.product_code,
        'product_name': new_product.product_name,
        'category_id': new_product.category_id,
        'cost': new_product.cost,
        'price': new_product.price,
        'current_stock': new_product.current_stock,
        'image': new_product.image,
        'message': 'Product added successfully!'
    }), 201

@app.route('/api/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found.'}), 404

    data = request.form
    product_code = data.get('product_code')
    product_name = data.get('product_name')
    category_id = data.get('category_id')
    cost = data.get('cost')
    price = data.get('price')
    current_stock = data.get('current_stock')

    # Validate required fields
    if not product_code or not product_name or not category_id or not cost or not price or not current_stock:
        return jsonify({'error': 'All fields are required.'}), 400

    # Update fields
    product.product_code = product_code
    product.product_name = product_name
    product.category_id = category_id
    product.cost = float(cost)
    product.price = float(price)
    product.current_stock = int(current_stock)

    # Handle product image
    image_file = request.files.get('image')
    if image_file:
        if allowed_file(image_file.filename):
            # Delete old product image if it's not the default
            if product.image and product.image != 'default.png':
                delete_image(product.image)
            # Save new product image
            product.image = save_image(image_file)
        else:
            return jsonify({'error': 'Invalid file type for product image.'}), 400

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update product.', 'details': str(e)}), 500

    return jsonify({
        'id': product.id,
        'product_code': product.product_code,
        'product_name': product.product_name,
        'category_id': product.category_id,
        'cost': product.cost,
        'price': product.price,
        'current_stock': product.current_stock,
        'image': product.image,
        'message': 'Product updated successfully!'
    }), 200

@app.route('/api/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found.'}), 404

    try:
        # Delete product image if it's not the default
        if product.image and product.image != 'default.png':
            delete_image(product.image)

        db.session.delete(product)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete product.', 'details': str(e)}), 500

    return jsonify({'message': 'Product deleted successfully!'}), 200

def allowed_file(filename):
    """Check if the file has an allowed extension."""
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_image(file):
    """Save the uploaded product image and return the filename."""
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    # Get the current date and time formatted as YYYYMMDD_HHMMSS
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    # Get the file extension
    ext = file.filename.rsplit('.', 1)[1].lower()

    # Generate a unique filename using the timestamp and a UUID
    unique_filename = f"{timestamp}_{uuid.uuid4().hex}.{ext}"
    filename = secure_filename(unique_filename)

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    return filename  # Return only the filename


def delete_image(filename):
    """Delete an image file from the upload folder."""
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        os.remove(file_path)
