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
    user_name = data.get('customerName', 'Unknown Customer')
    user_id = data.get('userId', 'Unknown id')
    order_date = data.get('timestamp')
    
    # Convert received_amount to float
    received_amount = float(data.get('receivedAmount', 0.0))  # Ensure it's a float
    total_amount = float(data.get('totalAmount', 0.0)) 
    print(total_amount) # Ensure it's a float
    discount = float(data.get('discount', 0.0))  # Get the discount from the request

    # Calculate total cost before discount
    total_cost_before_discount = sum(item['price'] * item['quantity'] for item in cart)

    # Apply discount
    discount_amount = (discount / 100) * total_cost_before_discount
    total_cost_after_discount = total_cost_before_discount - discount_amount

    # Apply tax (10%)
    tax_rate = 0.10
    tax_amount = total_cost_after_discount * tax_rate
    total_cost = total_cost_after_discount + tax_amount

    # Calculate change
    change = received_amount - total_cost

    # Prepare Telegram Message
    customer_details = (
        f"📅 <b>Date:</b> {order_date}\n"
        f"👤 <b>User:</b>\n"
        f"    • <b>ID  :</b> {user_id}\n"
        f"    • <b>Name:</b> {user_name}\n"
        f"____________________________\n"
        f"🛒 <b>Ordered Products:</b>\n"
    )

    full_message = customer_details

    for index, product in enumerate(cart, start=1):
        product_name = product.get('product_name', 'Unknown Product')
        price = product.get('price', 0.0)
        quantity = product.get('quantity', 1)
        item_total = price * quantity

        product_details = (
            f"  {index}. <b>{product_name}</b>\n"
            f"      • <b>Product ID:</b> {product.get('id', 'N/A')}\n"
            f"      • <b>Price:</b> ${price:.2f}\n"
            f"      • <b>Quantity:</b> {quantity}\n"
            f"      • <b>Subtotal:</b> ${(item_total):.2f}\n"
        )
        full_message += product_details
    full_message += f"____________________________" \
                    f"\n💲 <b>Total Cost:</b> ${total_cost_before_discount:.2f}\n" \
                    f"🎉 <b>Discount:</b> {discount}%\n"\
                    f"🏛️ <b>Total w/10% Tax:</b> ${total_cost:.2f}\n" \
                    f"💵 <b>Received Amount:</b> ${received_amount:.2f}\n" \
                    f"💰 <b>Change:</b> ${change:.2f}\n" \
                      # Add discount percentage to the message

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

    return jsonify({'status': 'success', 'change': change}), 201  # Return change in the response
