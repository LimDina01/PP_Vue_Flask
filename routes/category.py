from flask import request, jsonify
from app import app
from sqlalchemy import create_engine, text

# Create a database engine
engine = create_engine("mysql+mysqlconnector://root:@127.0.0.1/ppflask")

@app.route('/api/categories', methods=['GET'])
def get_categories():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT * FROM categories"))
        categories = result.fetchall()
        category_list = [
            {
                'id': category[0],
                'name': category[1],
                'description': category[2]
            }
            for category in categories
        ]
    return jsonify(category_list)

@app.route('/api/categories', methods=['POST'])
def add_category():
    data = request.form
    name = data.get('name')
    description = data.get('description')

    if not name or not description:
        return jsonify({'error': 'Name and description are required.'}), 400

    query = text("""
        INSERT INTO `categories` (name, description)
        VALUES (:name, :description)
    """)

    with engine.connect() as connection:
        result = connection.execute(query, {
            'name': name,
            'description': description
        })
        connection.commit()

        # Fetch the newly created category
        new_category_id = result.lastrowid
        new_category = connection.execute(text("SELECT * FROM categories WHERE id = :id"), {'id': new_category_id}).fetchone()

    return jsonify(dict(new_category._mapping)), 201

@app.route('/api/categories/<int:category_id>', methods=['PUT'])
def update_category(category_id):
    data = request.form
    name = data.get('name')
    description = data.get('description')

    if not name or not description:
        return jsonify({'error': 'Name and description are required.'}), 400

    query = text("""
        UPDATE `categories`
        SET name = :name, description = :description
        WHERE id = :category_id
    """)

    with engine.connect() as connection:
        connection.execute(query, {
            'name': name,
            'description': description,
            'category_id': category_id
        })
        connection.commit()

        # Fetch the updated category
        updated_category = connection.execute(text("SELECT * FROM categories WHERE id = :id"), {'id': category_id}).fetchone()

    return jsonify(dict(updated_category._mapping)), 200

@app.route('/api/categories/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    query = text("DELETE FROM `categories` WHERE `id` = :category_id")

    with engine.connect() as connection:
        connection.execute(query, {"category_id": category_id})
        connection.commit()

    return jsonify({'message': 'Category deleted successfully!'}), 200
