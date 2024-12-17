from flask import request, jsonify
from app import app
from sqlalchemy import create_engine, text
import os
from werkzeug.utils import secure_filename
import uuid
import datetime
from PIL import Image

# Configuration for file uploads
# app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'static', 'admin', 'assets', 'images')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Create a database engine
engine = create_engine("mysql+mysqlconnector://root:@127.0.0.1/ppflask")


def allowed_file(filename):
    """Check if the file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_product_image(file):
    """Save the uploaded product image and return the filename."""
    main_img_folder = os.path.join(os.getcwd(), 'static', 'admin', 'assets', 'images', 'main_img')
    sub_img_folder = os.path.join(os.getcwd(), 'static', 'admin', 'assets', 'images', 'sub_img')

    # Ensure directories exist
    if not os.path.exists(main_img_folder):
        os.makedirs(main_img_folder)
    if not os.path.exists(sub_img_folder):
        os.makedirs(sub_img_folder)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    ext = file.filename.rsplit('.', 1)[1].lower()
    unique_filename = f"{timestamp}_{uuid.uuid4().hex}.{ext}"
    filename = secure_filename(unique_filename)

    # Save the original image to main_img
    main_img_path = os.path.join(main_img_folder, filename)
    file.save(main_img_path)

    # Create a compressed version for sub_img
    with Image.open(main_img_path) as img:
        img.thumbnail((300, 300))  # Resize to a smaller size
        sub_img_path = os.path.join(sub_img_folder, filename)
        img.save(sub_img_path, quality=60, optimize=True)  # Save with compression

    return filename


@app.route('/api/products', methods=['POST'])
def add_product():
    # Check if the request contains the file part
    if 'image' not in request.files:
        return jsonify({'error': 'No image file part'}), 400

    file = request.files['image']
    if file and allowed_file(file.filename):
        image_filename = save_product_image(file)
    else:
        image_filename = 'default.png'

    # Extract other form data
    product_code = request.form.get('product_code')
    product_name = request.form.get('product_name')
    category_id = request.form.get('category_id')
    cost = request.form.get('cost')
    price = request.form.get('price')
    current_stock = request.form.get('current_stock')

    # Validate required fields
    if not product_code or not product_name or not category_id:
        return jsonify({'error': 'Product code, name, and category are required fields.'}), 400

    query = text("""
        INSERT INTO `products` (product_code, product_name, category_id, cost, price, current_stock, image)
        VALUES (:product_code, :product_name, :category_id, :cost, :price, :current_stock, :image)
    """)

    with engine.connect() as connection:
        result = connection.execute(query, {
            'product_code': product_code,
            'product_name': product_name,
            'category_id': category_id,
            'cost': cost,
            'price': price,
            'current_stock': current_stock,
            'image': image_filename
        })
        connection.commit()

        # Fetch the newly created product
        new_product_id = result.lastrowid
        new_product = connection.execute(
            text("SELECT * FROM products WHERE id = :id"),
            {'id': new_product_id}
        ).fetchone()

    return jsonify(dict(new_product._mapping)), 201


@app.route('/api/products', methods=['GET'])
def get_products():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT * FROM products"))
        products = result.fetchall()
        product_list = [
            {
                'id': product[0],
                'product_code': product[1],
                'product_name': product[2],
                'category_id': product[3],
                'cost': product[4],
                'price': product[5],
                'current_stock': product[6],
                'image': product[7]
            }
            for product in products
        ]
    return jsonify(product_list)


@app.route('/api/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    file = request.files.get('image')
    if file and allowed_file(file.filename):
        image_filename = save_product_image(file)
    else:
        with engine.connect() as connection:
            current_product = connection.execute(
                text("SELECT image FROM products WHERE id = :id"),
                {'id': product_id}
            ).fetchone()
            image_filename = current_product._mapping['image'] if current_product else 'default.png'

    product_code = request.form.get('product_code')
    product_name = request.form.get('product_name')
    category_id = request.form.get('category_id')
    cost = request.form.get('cost')
    price = request.form.get('price')
    current_stock = request.form.get('current_stock')

    if not product_code or not product_name or not category_id:
        return jsonify({'error': 'Product code, name, and category are required fields.'}), 400

    query = text("""
        UPDATE `products`
        SET product_code = :product_code, product_name = :product_name, category_id = :category_id,
            cost = :cost, price = :price, current_stock = :current_stock, image = :image
        WHERE id = :product_id
    """)

    with engine.connect() as connection:
        connection.execute(query, {
            'product_code': product_code,
            'product_name': product_name,
            'category_id': category_id,
            'cost': cost,
            'price': price,
            'current_stock': current_stock,
            'image': image_filename,
            'product_id': product_id
        })
        connection.commit()

        updated_product = connection.execute(
            text("SELECT * FROM products WHERE id = :id"),
            {'id': product_id}
        ).fetchone()

    return jsonify(dict(updated_product._mapping))


@app.route('/api/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    query = text("DELETE FROM `products` WHERE `id` = :product_id")

    with engine.connect() as connection:
        connection.execute(query, {"product_id": product_id})
        connection.commit()

    return jsonify({'message': 'Product deleted successfully!'}), 200
