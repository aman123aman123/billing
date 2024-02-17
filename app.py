from flask import Flask, Response, render_template, request, make_response, redirect, session
from pyzbar import pyzbar
import cv2
from flask_ngrok import run_with_ngrok
import numpy as np

import code128
import os, json, random
from barcode import generate
from barcode.codex import Code39

import winsound, csv

from io import TextIOWrapper

# https://www.perplexity.ai/search/create-a-nested-W4hbR477QTOylqe.3djvkw?s=c#3cc09b57-a1a2-40cf-9263-dd6e2dfd726b

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

DATABASE = 'postgresql://postgres:aman123@localhost:5433/postgres'

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
# db.init_app(app)  # uncomment this when you run the project for the first time then comment it
# https://www.perplexity.ai/search/how-to-use-bVdC.G8GTlmoFt3rctfhBw?s=u
run_with_ngrok(app)

app.secret_key = 'aman is great'

camera=cv2.VideoCapture(0) 
  
camera_on = False
bill = set()
current_order_id = 0

def generate_frames():
    global camera_on 
    global bill
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
                        bill.add(barcode_data)
                        print('session: ', bill)
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

    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))

    def __repr__(self) -> str:
        return f"{self.barcode} - {self.name}"

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'price': self.price,
            'quantity': self.quantity,
            'barcode': self.barcode,
        }

class Category(db.Model):
    __tablename__ = 'category'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    code = db.Column(db.String, nullable=False)

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_date = db.Column(db.DateTime, nullable=False, default=datetime.now())
    order_total = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String, nullable=False, default='cash')
    payment_status = db.Column(db.String, nullable=False, default='pending')
    
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"))

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"))
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"))
     
    quantity = db.Column(db.Float, nullable=False)
    price_per_quantity = db.Column(db.Float, nullable=False)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
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
        categories = Category.query.all()
        if prod_id is None:
            return render_template("products/add-update.html", categories=categories)
        else:
            product = Product.query.get(prod_id)
            category = Category.query.get(product.category_id)
        
            return render_template("products/add-update.html", product=product, prod_id=prod_id, categories=categories, cat_code=category.code)
    else:
        name=request.form["name"]
        price=request.form["price"]
        quantity=request.form["quantity"]
        category=request.form["category"]
        print(category)
        barcode=request.form["barcode"]
        selectedCategory = Category.query.filter_by(code=category).first()
        print(selectedCategory)
        if prod_id is None:
            new_product = Product(name=name, price=price, quantity=quantity, barcode=barcode, category_id=selectedCategory.id)
            db.session.add(new_product)
            db.session.commit()
            print(new_product)
            generate(barcode, category)
            
            return redirect('/products')
        else:
            product = Product.query.get(prod_id)
            product.price = price
            product.quantity = quantity
            if product.category_id != selectedCategory.id or product.name != name:
                product.name = name
                product.category_id = selectedCategory.id
                product.barcode = barcode
                generate(barcode, category)
            db.session.commit()
    
            return redirect('/products')

@app.route('/products/delete/<int:prod_id>')
def delete_product(prod_id):
    product = Product.query.get(prod_id)
    category = Category.query.get(product.category_id)
    delete(product.barcode, category.code)
    db.session.delete(product)
    db.session.commit()
    return redirect('/products')
  
# Define the path to the static folder
static_folder = os.path.join(app.root_path, 'static')

def generate(barcode, folder):
    print('creating new barcode')
    path = 'images/barcodes/'+folder
    if not os.path.exists(path):
        new_folder_path = os.path.join(static_folder, path)
        print('NFP:',new_folder_path)
        os.makedirs(new_folder_path, exist_ok=True)
    Code39(barcode).save(f"static/{path}/{barcode}")
    print('New Barcode Saved:', barcode)


@app.route('/delete_barcode', methods=['POST'])
def delete_barcode():
    data = request.get_json()
    barcode = data['barcode']
    category = data['category']
    delete(barcode, category)
    return {'message': 'success'}
    
def delete(barcode, category):
    file_path = os.path.join(static_folder, f'images/barcodes/{category}/{barcode}.svg')
    # Check if the file exists
    print(file_path)
    if os.path.exists(file_path):
        # Delete the file
        os.remove(file_path)
        print('Barcode Deleted:', barcode)
    print('Barcode Not Found')

@app.route('/categories')
def categories():
    categories = Category.query.all()
    sorted_categories = sorted(categories, key=lambda x: x.id)
    return render_template('categories/categories.html', categories=sorted_categories)

@app.route('/category/add-update', defaults={'cat_id': None}, methods=["POST","GET"])
@app.route('/category/add-update/<cat_id>',methods=["POST","GET"])
def add_update_category(cat_id):
    if request.method == 'GET':
        if cat_id is None:
            return render_template('/categories/add-update.html')
        else:
            category = Category.query.get(cat_id)
            return render_template('/categories/add-update.html', category=category, cat_id=cat_id)
    else:
        name = request.form['name']
        code = request.form['code']
        if cat_id is None:
            new_category = Category(name=name, code=code)      
            db.session.add(new_category)
            db.session.commit()
            return redirect('/categories')
        else:
            category = Category.query.get(cat_id)
            print(category)
            category.name = name
            category.code = code
            db.session.commit()
            return redirect('/categories')

@app.route('/category/delete/<int:cat_id>')
def delete_category(cat_id):
    category = Category.query.get(cat_id)
    db.session.delete(category)
    db.session.commit()
    return redirect('/categories')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/toggle_camera')
def toggle_camera():
    global camera_on
    camera_on = not camera_on
    return redirect('/create-bill')

@app.route('/create-bill')
def create_bill():
    print('bill', bill)
    products = []
    for b in bill:
        prod = Product.query.filter_by(barcode=b).first()
        if prod is not None:
            products.append(prod)
    customers = Customer.query.all()
    products_json = json.dumps([product.serialize() for product in products])
    return render_template('/bill/create-bill.html', bill=bill, products=products, customers=customers, products_json=products_json)

@app.route('/remove-product-from-bill', methods=['POST'])
def remove_product_from_bill():
    data = request.get_json()
    print('delete:',data)
    barcode = data['barcode']
    print('delete:',barcode)
    bill.discard(barcode)
    print('NewBill:',bill)
    return {'message':'successfully deleted'}

@app.route('/save-bill', methods=['POST'])
def save_bill():
    global current_order_id

    data = request.get_json()
    customerType = data['customerType']
    customerId = int(data['customerId'])
    customerDetails = data['customerDetails']
    totalBill = float(data['totalBill'])
    productList = data['productList']

    customer = getCustomer(customerType, customerId, customerDetails)
    print('CID:',customer.id, customer.name)

    order = Order(order_total=totalBill,customer_id=customer.id)
    db.session.add(order)
    db.session.commit()
    current_order_id = order.id
    print('Order:',order.id)

    for prod in productList:
        product = OrderItem(product_id=prod["id"], quantity=prod["quantity"], price_per_quantity=prod["pricePerQuantity"], order_id=order.id)
        db.session.add(product)
    db.session.commit()

    global bill
    bill.clear()

    return {'message':'successfully saved'}

@app.route('/show-bill')
def show_bill():
    global current_order_id
    order = Order.query.get(current_order_id)
    customer = Customer.query.get(order.customer_id)

    data = db.session.query(Product.name, OrderItem.quantity, OrderItem.price_per_quantity).join(OrderItem).join(Order).filter(Order.id == order.id).group_by(Product.name, OrderItem.quantity, OrderItem.price_per_quantity).all()
    print('data:', data)   
    
    return render_template('bill/show-bill.html', order=order, customer=customer, ordered_products=data)

@app.route('/update-payment-method', methods=['POST'])
def update_payment_method():
    global current_order_id
    data = request.get_json()
    order = Order.query.get(current_order_id)
    order.payment_method = data['payment_method']
    order.payment_status = 'paid'
    db.session.commit()
    return {'status': 'success'}


def getCustomer(customerType, customerId, customerDetails):    
    if (customerType == 'existing' and customerId != 0):
        customer = Customer.query.get(customerId)
        return customer
    else:
        new_customer = Customer(name=customerDetails['name'], phone=customerDetails['mobile'], address=customerDetails['address'])
        db.session.add(new_customer)
        db.session.commit()
        return new_customer

@app.route('/import-export')
def import_export():
    return render_template('data/import_export.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part'

    file = request.files['file']

    if file.filename == '':
        return 'No selected file'

    if file:
        csv_file = TextIOWrapper(file, encoding='utf-8')
        csv_reader = csv.reader(csv_file)
        
        for row in csv_reader:
            print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]}")
            cat_id = int(row[3])
            barcode = create_barcode(row[0], cat_id)
            product = Product(name=row[0], price=int(row[1]), quantity=int(row[2]), barcode=barcode, category_id=cat_id)
            db.session.add(product)

        db.session.commit()

        return 'File uploaded successfully'

    return 'Error uploading file'

def create_barcode(name, cat_id):
    date = datetime.now()
    month = date.month
    if month < 10:
        month = '0' + str(month)
    year = str(date.year - 2000)
    batch = month + year
    three_digit_random_number = str(random.randint(100, 999))
    category = Category.query.get(cat_id)
    code = category.code.upper() + name[:3].upper() + batch + three_digit_random_number
    print(code, category.code)
    generate(code, category.code)

    return code

"""
https://www.perplexity.ai/search/how-to-write-T4gKu1wEQaO.51aI2O_RJg?s=c#539e7856-c9dc-49ea-8d3e-a7431c7382e2

"""

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

'''
Bill Form with Customer Information
Bulk Data CSV
Customer wise Bill Information
    /customers/bills/arshad/billNo
Send Invoice via Whatsapp

Payment Information & Status

Search Box for Products, Customers
'''