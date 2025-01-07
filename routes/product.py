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


def get_db_connection():
    engine = create_engine("mysql+mysqlconnector://root:@127.0.0.1/ppflask")
    connection = engine.connect()
    return connection


@app.route('/pos_products', methods=['GET'])
def get_products_pos():
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


@app.route('/api/sales', methods=['POST'])
def create_sale():
    data = request.get_json()

    # Extract sale items
    sale_items = data.get('saleItems', [])
    total_amount = data.get('totalAmount')
    received_amount = data.get('receivedAmount')
    user_id = data.get('userId', 'Unknown id')  
    transaction_date = datetime.datetime.now()
    full_price = data.get('price', 0.0) 
    discount = data.get('discount', 0.0)  # Extract discount value

    # Generate a unique reference code for the sale
    ref_code = str(uuid.uuid4())

    # Insert the sale into the sales table
    insert_sale_query = text(""" 
        INSERT INTO sales (ref_code, total_amount, amount_after_tax, received_amount, discount, user_id, transaction_date)
        VALUES (:ref_code, :total_amount, :amount_after_tax, :received_amount, :discount, :user_id, :transaction_date)
    """)

    with engine.connect() as connection:
        # Start a transaction
        with connection.begin():
            connection.execute(insert_sale_query, {
                'ref_code': ref_code,
                'total_amount': full_price,
                'amount_after_tax': total_amount,
                'received_amount': received_amount,
                'discount': discount,
                'user_id': user_id,
                'transaction_date': transaction_date,
            })

            # Get the last inserted sale ID
            sale_id = connection.execute(text("SELECT LAST_INSERT_ID()")).scalar()

            # Insert sale items into the sale_items table
            insert_sale_item_query = text(""" 
                INSERT INTO sale_items (sales_id, product_id, product_name, price, quantity)
                VALUES (:sales_id, :product_id, :product_name, :price, :quantity)
            """)

            for item in sale_items:
                # Directly execute the insert query without checking for keys
                connection.execute(insert_sale_item_query, {
                    'sales_id': sale_id,
                    'product_id': item['id'],
                    'product_name': item['product_name'],
                    'price': item['price'],
                    'quantity': item['quantity'],
                })

    return jsonify({'message': 'Sale recorded successfully!', 'sale_id': sale_id}), 201


@app.route('/api/sales', methods=['GET'])
def get_sales():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT * FROM sales"))
        sales = result.fetchall()
        sales_list = [
            {
                'id': sale[0],
                'ref_code': sale[1],
                'total_amount': sale[2],
                'amount_after_tax': sale[3],
                'received_amount': sale[4],
                'discount': sale[5],
                'user_id': sale[6],
                'transaction_date': sale[7]
            }
            for sale in sales
        ]

    return jsonify(sales_list)


@app.route('/api/sales/<int:sale_id>', methods=['GET'])
def get_sale_details(sale_id):
    with engine.connect() as connection:
        # Fetch the sale details
        sale_query = text("SELECT * FROM sales WHERE id = :sale_id")
        sale = connection.execute(sale_query, {'sale_id': sale_id}).fetchone()

        # Fetch the sale items
        items_query = text("SELECT * FROM sale_items WHERE sales_id = :sale_id")
        items = connection.execute(items_query, {'sale_id': sale_id}).fetchall()

        # Prepare the response
        sale_details = {
            'id': sale[0],
            'ref_code': sale[1],
            'total_amount': sale[2],
            'amount_after_tax': sale[3],
            'received_amount': sale[4],
            'discount': sale[5],
            'user_id': sale[6],
            'transaction_date': sale[7],
            'items': [{'id': item[0], 'product_name': item[2], 'quantity': item[3], 'price': item[4]} for item in items]  # Adjust indices based on your table structure
        }

    return jsonify(sale_details)