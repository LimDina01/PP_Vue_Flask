from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from app import app
from app import db


class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False, unique=True)
    description = db.Column(db.String(255))


@app.route('/api/categories', methods=['GET'])
def get_categories():
    categories = Category.query.all()
    return jsonify([{
        'id': category.id,
        'name': category.name,
        'description': category.description
    } for category in categories])


@app.route('/api/categories', methods=['POST'])
def add_category():
    data = request.form
    name = data.get('name')
    description = data.get('description')

    if not name or not description:
        return jsonify({'error': 'Name and description are required.'}), 400

    new_category = Category(name=name, description=description)
    db.session.add(new_category)
    db.session.commit()

    return jsonify({
        'id': new_category.id,
        'name': new_category.name,
        'description': new_category.description
    }), 201


@app.route('/api/categories/<int:category_id>', methods=['PUT'])
def update_category(category_id):
    data = request.form
    category = Category.query.get(category_id)

    if not category:
        return jsonify({'error': 'Category not found.'}), 404

    category.name = data.get('name')
    category.description = data.get('description')
    db.session.commit()

    return jsonify({
        'id': category.id,
        'name': category.name,
        'description': category.description
    }), 200






@app.route('/api/categories/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    category = Category.query.get(category_id)
    if not category:
        return jsonify({'error': 'Category not found.'}), 404

    try:
        db.session.delete(category)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete category.', 'details': str(e)}), 500

    return jsonify({'message': 'Category deleted successfully!'}), 200
