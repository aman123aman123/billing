from flask import Flask, Response, render_template, request, make_response, redirect
from pyzbar import pyzbar
import cv2
from flask_ngrok import run_with_ngrok
import numpy as np

import winsound

# https://www.perplexity.ai/search/create-a-nested-W4hbR477QTOylqe.3djvkw?s=c#3cc09b57-a1a2-40cf-9263-dd6e2dfd726b

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

DATABASE = 'postgresql://postgres:aman123@localhost:5433/postgres'

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
# db.init_app(app)
# https://www.perplexity.ai/search/how-to-use-bVdC.G8GTlmoFt3rctfhBw?s=u

run_with_ngrok(app)

camera=cv2.VideoCapture(0)

camera_on = False

def generate_frames():
    global camera_on
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            if camera_on:

                # Convert the frame to grayscale for barcode detection
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                # Find barcodes in the frame
                barcodes = pyzbar.decode(gray)

                # Process detected barcodes
                for barcode in barcodes:
                    # Extract barcode data
                    barcode_data = barcode.data.decode('utf-8')
                    if barcode_data:
                        print(barcode_data)
                        winsound.Beep(750, 500)
                        break

                # if barcodes:
                #     print(barcodes)
                #     break

                # Encode the frame as JPEG
                _, jpeg = cv2.imencode('.jpg', frame)
                frame_bytes = jpeg.tobytes()
                yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n\r\n')

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    
    def __repr__(self):
        return '<User %r>' % self.name


class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    address = db.Column(db.String, nullable=False)
    phone = db.Column(db.Integer, nullable=False)

    def __repr__(self) -> str:
        return f"User: {self.name}"

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    barcode = db.Column(db.String, nullable=False)

    def __repr__(self) -> str:
        return f"{self.barcode} - {self.name}"

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_date = db.Column(db.DateTime, nullable=False, default=datetime.now())
    order_total = db.Column(db.Integer, nullable=False)
    
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"))

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"))
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"))
    
    quantity = db.Column(db.Integer, nullable=False)
    price_per_quantity = db.Column(db.Integer, nullable=False)

# with app.app_context():
#     db.create_all()

@app.route('/create_user', methods=['POST'])
def create_user():
    data = request.get_json()
    new_user = User(name=data['name'])
    db.session.add(new_user)
    db.session.commit()
    return make_response({"message": "new user created"}, 201)

@app.route('/user')
def get_user():
    users = User.query.all()
    user_list = [
        {'id': user.id, 'name': user.name} for user in users
    ]
    return render_template('users.html', users=user_list) 

@app.route('/update-user/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = User.query.get(user_id)
    data = request.get_json()
    user.name = data['name']
    db.session.commit()
    return make_response({'success': True}, 200)

@app.route('/delete-user/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get(user_id)
    db.session.delete(user)
    db.session.commit()
    return make_response({'message': 'deleted'}, 200)

@app.route('/')
def index():
    result = User.query.all()
    # print(result)
    return render_template("home.html")


@app.route('/products')
def products():
    products = Product.query.all()
    sorted_products = sorted(products, key=lambda x: x.id)
    return render_template("products/products.html", products=sorted_products)

@app.route('/products/add-update', defaults={'prod_id': None}, methods=["POST","GET"])
@app.route('/products/add-update/<prod_id>',methods=["POST","GET"])
def add_update_product(prod_id):
    if request.method=="GET":
        if prod_id is None:
            return render_template("products/add-update.html")
        else:
            product = Product.query.get(prod_id)
            return render_template("products/add-update.html", product=product, prod_id=prod_id)
    else:
        name=request.form["name"]
        price=request.form["price"]
        quantity=request.form["quantity"]
        barcode=request.form["barcode"]
        if prod_id is None:
            new_product = Product(name=name, price=price, quantity=quantity, barcode=barcode)
            db.session.add(new_product)
            db.session.commit()
            print(new_product)
            return make_response({'success': True}, 201)

        else:
            product = Product.query.get(prod_id)

            product.name = name
            product.price = price
            product.quantity = quantity
            product.barcode = barcode
            db.session.commit()
            print(request.form["name"],prod_id)
            return redirect('/products')

@app.route('/products/delete/<int:prod_id>')
def delete_product(prod_id):
    product = Product.query.get(prod_id)
    db.session.delete(product)
    db.session.commit()
    return redirect('/products')


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/toggle_camera')
def toggle_camera():
    global camera_on
    camera_on = not camera_on
    return redirect('/')
             
if __name__ == '__main__':
    app.run(debug=True)

# Category  Product Batch   Quantity
# VEG       TOM     B224    01
# VEG       TOM     B224    02

"""
Fruits & Vegetables
Bakery & Cereals
Dairy & Eggs
Meat & Seafood
Packaged Foods
Beverages
Household Items
Personal Care
"""