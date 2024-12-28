from flask import request, jsonify
from app import app
from sqlalchemy import create_engine, text
import os
from werkzeug.utils import secure_filename
import uuid
import datetime
from PIL import Image
import requests

@app.route('/api/pay', methods=['POST'])
def save_print():
    data = request.get_json()
    cart = data.get('carts', [])
    customer_name = data.get('customerName', 'Unknown Customer')
    phone = data.get('phone', 'No Phone Provided')
    order_date = data.get('timestamp')

    # Prepare Telegram Message
    customer_details = (
        f"📅 <b>Date:</b> {order_date}\n"
        f"👤 <b>Customer:</b>\n"
        f"    • <b>Name:</b> {customer_name}\n"
        f"    • <b>Phone:</b> {phone}\n"
        f"____________________________\n"
        f"🛒 <b>Ordered Products:</b>\n"
    )

    full_message = customer_details

    for index, product in enumerate(cart, start=1):
        product_name = product.get('product_name', 'Unknown Product')  # Safely get the product name
        price = product.get('price', 0.0)  # Safely get the price, default to 0.0
        quantity = product.get('quantity', 1)  # Safely get the quantity, default to 1
        item_total = price * quantity

        product_details = (
            f"  {index}. <b>{product_name}</b>\n"
            f"      • <b>Product ID:</b> {product.get('id', 'N/A')}\n"  # Safely get the product ID
            f"      • <b>Price:</b> ${price:.2f}\n"
            f"      • <b>Quantity:</b> {quantity}\n"
            f"      • <b>Subtotal:</b> ${(item_total):.2f}\n"
        )
        full_message += product_details

    full_message += f"____________________________" \
                    f"\n💰 <b>Total Cost:</b> ${sum(item['price'] * item['quantity'] for item in cart):.2f}\n"

    # Send message to Telegram
    bot_token = '7143441148:AAG1H4JXVuNJbRU5X03_GrqTpEMvDCPQoj0'
    chat_id = '837489345'
    
    response = requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage", data={
        'chat_id': chat_id,
        'text': full_message,
        'parse_mode': 'HTML'
    })

    if response.status_code != 200:
        return jsonify({'status': 'error', 'message': 'Failed to send notification to Telegram'}), 500

    return jsonify({'status': 'success'}), 201
