from flask import Flask, Response, render_template, request, redirect, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from pyzbar import pyzbar
import cv2
from flask_ngrok import run_with_ngrok
import numpy as np
from apyori import apriori
import os, json, random, requests, razorpay
from barcode import generate
from barcode.codex import Code39
import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import winsound, csv

from io import TextIOWrapper
from dotenv import load_dotenv

load_dotenv()

# https://www.perplexity.ai/search/create-a-nested-W4hbR477QTOylqe.3djvkw?s=c#3cc09b57-a1a2-40cf-9263-dd6e2dfd726b

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

DATABASE = os.getenv('DATABASE_URL')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
@login_manager.user_loader

def load_user(user_id):
    return User.query.get(int(user_id))

@login_manager.unauthorized_handler
def unauthorized_callback():
    if current_user.is_anonymous:
        flash('You are not logged in', 'warning')
        return redirect('/login')

# db.init_app(app)  # uncomment this when you run the project for the first time then comment it
# https://www.perplexity.ai/search/how-to-use-bVdC.G8GTlmoFt3rctfhBw?s=u
run_with_ngrok(app)

app.secret_key = os.getenv('APP_SECRET_KEY')

sender_email = os.getenv('SMTP_SENDER_EMAIL')
smtp_server = os.getenv('SMTP_SERVER')
smtp_port = os.getenv('SMTP_PORT')
smtp_username = os.getenv('SMTP_USERNAME')
smtp_password = os.getenv('SMTP_PASSWORD')


TEST_API_KEY = os.getenv('RAZORPAY_TEST_API_KEY')
TEST_API_SECRET_KEY = os.getenv('RAZORPAY_TEST_API_SECRET_KEY')

client = razorpay.Client(auth=(TEST_API_KEY, TEST_API_SECRET_KEY))

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
  
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    phone = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)
    def __repr__(self) -> str:
        return f"User: {self.name}"
    
class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    phone = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False)
    address = db.Column(db.String, nullable=False)
    def __repr__(self) -> str:
        return f"Customer: {self.name}"

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price_per_quantity = db.Column(db.Float, nullable=False)
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

    def __repr__(self) -> str:
        return f"#{self.id} | O:{self.order_id} | P:{self.product_id} | Q:{self.quantity}"

# with app.app_context():
#     db.create_all()

@app.route('/')
def index():
    # send_bill_email()
    return render_template("home.html", current_user=current_user)
 
# https://www.digitalocean.com/community/tutorials/how-to-add-authentication-to-your-app-with-flask-login

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        try:   
            email = request.form.get('email')
            password = request.form.get('password')

            user = User.query.filter_by(email=email).first()

            if not user or not check_password_hash(user.password, password):
                flash('Invalid Credentials', 'danger')
                return redirect('/login')

            login_user(user)

            flash(f'Welcome back {user.name}', 'success')    
            return redirect('/')
        except:
            flash('Something went wrong', 'danger')
    else:
        return render_template('/auth/login.html', current_user=current_user)

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        try:
            email = request.form.get('email')
            name = request.form.get('name')
            phone = request.form.get('phone')
            password = request.form.get('password')

            user = User.query.filter_by(email=email).first()

            if user:
                flash('User Already Exists', 'warning')
                return redirect('/register')
            
            new_user = User(name=name, email=email, phone=phone, password=generate_password_hash(password))
            db.session.add(new_user)
            db.session.commit()
            flash(f'New User Created with Name: {name} & Email: {email}', 'success')

            return redirect('/login')
        except:
            flash('Something went wrong while Registering the new user', 'danger')
    else:
        return render_template('/auth/register.html', current_user=current_user)
        
@app.route('/logout')
def logout():
    logout_user()
    return redirect('/login')


@app.route('/bill-email')
def bill_email():
    order = Order.query.get(current_order_id)
    customer = Customer.query.get(order.customer_id)

    data = db.session.query(Product.name, OrderItem.quantity, Product.price_per_quantity).join(OrderItem).join(Order).filter(Order.id == order.id).group_by(Product.name, OrderItem.quantity, Product.price_per_quantity).all()
    # print("Data:", data)
    return  render_template('email/bill.html', order=order, customer=customer, ordered_products=data)

@app.route('/products')
@login_required
def products():
    try:
        products = Product.query.all()
        sorted_products = sorted(products, key=lambda x: x.id)
        return render_template("products/products.html", products=sorted_products, current_user=current_user)
    except:
        flash('COULD NOT FETCH PRODUCTS', 'danger')
        return redirect('/')

@app.route('/products/add-update', defaults={'prod_id': None}, methods=["POST","GET"])
@app.route('/products/add-update/<prod_id>',methods=["POST","GET"])
@login_required
def add_update_product(prod_id):
    try:
        if request.method=="GET":   
            categories = Category.query.all()
            if prod_id is None:
                return render_template("products/add-update.html", categories=categories, current_user=current_user)
            else:
                product = Product.query.get(prod_id)
                category = Category.query.get(product.category_id)
            
                return render_template("products/add-update.html", product=product, prod_id=prod_id, categories=categories, cat_code=category.code, current_user=current_user)
        else:
            name=request.form["name"]
            price=request.form["price"]
            quantity=request.form["quantity"]
            price_per_quantity=request.form["price_per_quantity"]
            category=request.form["category"]
            print(category)
            barcode=request.form["barcode"]
            selectedCategory = Category.query.filter_by(code=category).first()
            print(selectedCategory)
            if prod_id is None:
                code = generate(barcode, category)
                if code:
                    new_product = Product(name=name, price=price, quantity=quantity, price_per_quantity=price_per_quantity, barcode=code, category_id=selectedCategory.id)
                    db.session.add(new_product)
                    db.session.commit()
                    print(new_product)
                
                return redirect('/products')
            else:
                product = Product.query.get(prod_id)
                product.price = price
                product.quantity = quantity
                product.price_per_quantity = price_per_quantity
                if product.category_id != selectedCategory.id or product.name != name:
                    code = generate(barcode, category)
                    product.name = name
                    product.category_id = selectedCategory.id
                    if code:
                        product.barcode = code
                db.session.commit()
        
                return redirect('/products')
    except:
        flash('COULD NOT ADD/UPDATE PRODUCT', 'danger')
        return redirect('/products')

@app.route('/products/delete/<int:prod_id>')
@login_required
def delete_product(prod_id):
    try:
        product = Product.query.get(prod_id)
        category = Category.query.get(product.category_id)
        delete(product.barcode, category.code)
        db.session.delete(product)
        db.session.commit()
        return redirect('/products')
    except:
        flash('ERROR DELETING PRODUCT', 'danger')
        return redirect('/products')
  
# Define the path to the static folder
static_folder = os.path.join(app.root_path, 'static')

def generate(barcode, folder):
    try:
        print('creating new barcode')
        path = 'images/barcodes/'+folder
        if not os.path.exists(path):
            new_folder_path = os.path.join(static_folder, path)
            print('NFP:',new_folder_path)
            os.makedirs(new_folder_path, exist_ok=True)
        Code39(barcode).save(f"static/{path}/{str(Code39(barcode))}")
        print(f'barcode: {barcode} | Code39: {Code39(barcode)}')
        return str(Code39(barcode))
    except Exception:
        flash('Something went wrong creating Barcode', 'warning')
        print(Exception)


@app.route('/delete_barcode', methods=['POST'])
@login_required
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
@login_required
def categories():
    try:
        categories = Category.query.all()
        sorted_categories = sorted(categories, key=lambda x: x.id)
        return render_template('categories/categories.html', categories=sorted_categories, current_user=current_user)
    except:
        flash('ERROR FETCHING CATEGORIES', 'danger')
        return redirect('/')

@app.route('/category/add-update', defaults={'cat_id': None}, methods=["POST","GET"])
@app.route('/category/add-update/<cat_id>',methods=["POST","GET"])
@login_required
def add_update_category(cat_id):
    try:
        if request.method == 'GET':
            if cat_id is None:
                return render_template('/categories/add-update.html', current_user=current_user)
            else:
                category = Category.query.get(cat_id)
                return render_template('/categories/add-update.html', category=category, cat_id=cat_id, current_user=current_user)
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
    except:
        flash("COULDN'T ADD/UPDATE CATEGORY", 'danger')
        return redirect('/categories')

@app.route('/category/delete/<int:cat_id>')
@login_required
def delete_category(cat_id):
    try:
        category = Category.query.get(cat_id)
        db.session.delete(category)
        db.session.commit()
        return redirect('/categories')
    except:
        flash('ERROR DELETING CATEGORY', 'danger')
        return redirect('/categories')

@app.route('/video_feed')
@login_required
def video_feed():
    try:
        return Response(generate_frames(),mimetype='multipart/x-mixed-replace; boundary=frame')
    except:
        flash('ERROR READING CAMERA', 'danger')
        return redirect('/')

@app.route('/toggle_camera')
@login_required
def toggle_camera():
    global camera_on
    camera_on = not camera_on
    return redirect('/create-bill')

@app.route('/create-bill')
@login_required
def create_bill():
    try:
        global bill
        print('bill', bill, type(bill))
        if bill is None:
            return render_template('/bill/create-bill.html', current_user=current_user)
        products = []
        for b in bill:
            prod = Product.query.filter_by(barcode=b).first()
            if prod is not None:
                products.append(prod)
        customers = Customer.query.all()
        products_json = json.dumps([product.serialize() for product in products])
        return render_template('/bill/create-bill.html', bill=bill, products=products, customers=customers, products_json=products_json, current_user=current_user)
    except:
        print('ERROR WHILE CREATING BILL')
        flash(message="ERROR WHILE CREATING BILL", category="danger")
        return redirect('/')

@app.route('/remove-product-from-bill', methods=['POST'])
@login_required
def remove_product_from_bill():
    data = request.get_json()
    print('delete:',data)
    barcode = data['barcode']
    print('delete:',barcode)
    bill.discard(barcode)
    print('NewBill:',bill)
    return {'message':'successfully deleted'}

@app.route('/save-bill', methods=['POST'])
@login_required
def save_bill():
    try:
        global current_order_id
        global bill
        bill.clear()

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
            print()
            print(prod)
            item = OrderItem(product_id=prod["id"], quantity=prod["quantity"], order_id=order.id)
            db.session.add(item)
        db.session.commit()

        return {'message':'successfully saved'}
    except:
        flash('ERROR SAVING BILL', 'danger')
        return redirect('/create-bill')

@app.route('/show-bill')
@login_required
def show_bill():
    try:
        global current_order_id
        order = Order.query.get(current_order_id)
        customer = Customer.query.get(order.customer_id)

        data = db.session.query(Product.name, OrderItem.quantity, Product.price_per_quantity).join(OrderItem).join(Order).filter(Order.id == order.id).group_by(Product.name, OrderItem.quantity, Product.price_per_quantity).all()
        print('data:', data)   
        
        return render_template('bill/show-bill.html', order=order, customer=customer, ordered_products=data, current_user=current_user)
    except:
        flash('ERROR FETCHING BILL DETAILS', 'danger')
        return redirect('/create-bill')

@app.route('/update-payment-method', methods=['POST'])
@login_required
def update_payment_method():
    try:
        global current_order_id
        data = request.get_json()
        order = Order.query.get(current_order_id)
        order.payment_method = data['payment_method']
        if data['payment_method'] == 'cash':
            order.payment_status = 'paid'
            update_inventory(order.id)
            send_bill_email()
        db.session.commit()
        if data['payment_method'] == 'online':
            print('sending request to razorpay')
            requests.post('http://127.0.0.1:5000/payment', json={"amount": order.order_total})
        return {'status': 'success'}
    except:
        flash('ERROR UPDATING PAYMENT DETAILS', 'danger')
        return redirect('/show-bill')
        
def update_inventory(order_id):
    try:
        orderItem = OrderItem.query.filter_by(order_id = order_id).all()
        print('\n', orderItem)
        for item in orderItem:
            product = Product.query.get(item.product_id)
            quantity = product.quantity
            product.quantity = quantity - item.quantity
            print()
            print(product.name)
            print(f"{quantity} - {item.quantity} = {quantity - item.quantity}")
            db.session.add(product)
        db.session.commit() 
        print()
    except:
        flash("COULD NOT UPDATE INTVENTORY", "danger")

def getCustomer(customerType, customerId, customerDetails):
    try:
        if (customerType == 'existing' and customerId != 0):
            customer = Customer.query.get(customerId)
            return customer
        else:
            new_customer = Customer(name=customerDetails['name'], phone=customerDetails['mobile'], email=customerDetails['email'], address=customerDetails['address'])
            db.session.add(new_customer)
            db.session.commit()
            return new_customer
    except:
        flash('ERROR CREATING CUSTOMER', 'danger')
        return redirect('/save-bill')

@app.route('/import-export')
@login_required
def import_export():
    return render_template('data/import_export.html', current_user=current_user)

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    try:
        if 'file' not in request.files:
            flash('INVALID FILE TYPE', 'danger')
            return redirect('/import-export')

        file = request.files['file']

        if file.filename == '':
            flash('PLEASE SELECT A FILE TO UPLOAD', 'warning')
            return redirect('/import-export')

        if file:
            csv_file = TextIOWrapper(file, encoding='utf-8')
            csv_reader = csv.reader(csv_file)
            
            for row in csv_reader:
                print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]}| {row[4]}")
                cat_id = int(row[4])
                barcode = create_barcode(row[0], cat_id)
                if barcode:
                    product = Product(name=row[0], price=int(row[1]), quantity=int(row[2]), price_per_quantity=row[3], barcode=barcode, category_id=cat_id)
                    db.session.add(product)
                else:
                    print("An error occurred while creating product")
                    break

            db.session.commit()

            return redirect('/products')

        flash('ERROR UPLOADING FILE', 'danger')
        return redirect('/import-export')
    except:
        flash('PLEASE CHECK YOUR CSV FILE', 'danger')
        return redirect('/import-export')
        

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
    barcode = generate(code, category.code)

    return barcode


@app.route('/customers')
@login_required
def customers():
    try:
        customers = Customer.query.all()
        return render_template('/customers/customers.html', customers=customers, current_user=current_user)
    except:
        flash('ERROR GETTING CUSTOMERS', 'danger')
        return redirect('/')

@app.route('/customers/<int:cust_id>/bills')
@login_required
def customer_bills(cust_id):
    try:
        orders = Order.query.filter_by(customer_id=cust_id).all()
        print('ORD:', orders)
        return render_template('/customers/customer-bills.html', orders=orders, current_user=current_user)
    except:
        flash('ERROR GETTING CUSTOMER BILLS', 'danger')
        return redirect('/customers')

@app.route('/customers/<int:cust_id>/bills/order/<int:order_id>')
@login_required
def customer_order_bills(cust_id, order_id):
    try:
        customer = Customer.query.get(cust_id)
        order = Order.query.get(order_id)
        data = db.session.query(Product.name, OrderItem.quantity, Product.price_per_quantity).join(OrderItem).join(Order).filter(Order.id == order.id).group_by(Product.name, OrderItem.quantity, Product.price_per_quantity).all()

        return render_template('/customers/customer-bills-order.html', customer=customer, order=order, ordered_products=data, current_user=current_user)
    except:
        flash('ERROR: COULD NOT FIND THE RESOURCE YOU ARE LOOKING FOR', 'danger')
        return redirect('/customers')


orderId = ''
ORDER = {}
@app.route('/payment', methods=['POST'])
# @login_required
def payment():
    try:
        global ORDER
        data = request.get_json()
        print('AMOUNT:',data['amount'])
        amount = int(data['amount']) * 100 if data else 10000
        currency = 'INR'
        # notes = {'email': 'example@example.com'}
        # Create a Razorpay order
        ordr = client.order.create({'amount': amount, 'currency': currency}) #, 'notes': notes
        ORDER = ordr
        print(ORDER)
        return {'message':'success'}
    except:
        flash('ERROR CREATING PAYMENT ORDER', 'danger')
        return redirect('/show-bill')

@app.route('/show-payment')
@login_required
def show_payment():
    global ORDER
    global current_order_id
    order = Order.query.get(current_order_id)
    customer = Customer.query.get(order.customer_id)
    data = db.session.query(Product.name, OrderItem.quantity, Product.price_per_quantity).join(OrderItem).join(Order).filter(Order.id == order.id).group_by(Product.name, OrderItem.quantity, Product.price_per_quantity).all()

    return render_template('/payments/payment.html', rzp_order=ORDER, order=order, customer=customer, ordered_products=data, current_user=current_user)

@app.route('/capture', methods=['POST'])
# @login_required
def capture():
    try:
        global current_order_id
        payment_id = request.form['razorpay_payment_id']
        order_id = request.form['razorpay_order_id']
        signature = request.form['razorpay_signature']
        # Verify the payment signature
        params_dict = {
            'razorpay_payment_id': payment_id,
            'razorpay_order_id': order_id,
            'razorpay_signature': signature
        }
        print(params_dict)
        print(request,request.form)
        verifySignature = client.utility.verify_payment_signature(params_dict)
        if verifySignature:
            update_payment_status()
            update_inventory(current_order_id)
        # Capture the payment
        #client.payment.capture(payment_id, 1000)
        return redirect('/show-bill')
    except:
        flash('ERROR VERIFYING PAYMENT', 'danger')
        return redirect('/show-bill')

def update_payment_status():
    try:
        global current_order_id
        order = Order.query.get(current_order_id)
        order.payment_method = 'online'
        order.payment_status = 'paid'
        db.session.commit()
        send_bill_email()
    except:
        flash('ERROR UPDATING PAYMENT STATUS', 'danger')
        return redirect('/show-bill')
   
def send_bill_email():
    try:
        order = Order.query.get(current_order_id)
        customer = Customer.query.get(order.customer_id)

        data = db.session.query(Product.name, OrderItem.quantity, Product.price_per_quantity).join(OrderItem).join(Order).filter(Order.id == order.id).group_by(Product.name, OrderItem.quantity, Product.price_per_quantity).all()

        # Create a message
        message = MIMEMultipart()
        message['From'] = sender_email
        message['To'] = customer.email
        message['Subject'] = f"Order: #{order.id} | {customer.name} | T: Rs.{order.order_total}"
        message.attach(MIMEText(render_template('email/bill.html', order=order, customer=customer, ordered_products=data), 'html'))

        # Connect to the SMTP server
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Upgrade the connection to a secure TLS connection
        server.login(smtp_username, smtp_password)

        # Send the email
        # server.send_message(message)
        server.sendmail(sender_email, message['To'], message.as_string())
    
        # Close the connection
        server.quit()
        # return True, "Email sent successfully!"
        flash(f"An email has been sent to {customer.email}", 'success')
    except Exception as e:
        # return False, f"Error sending email: {str(e)}"
        flash('Could not send email', 'danger')

 
@app.route('/api/products', methods=['GET'])
def api_products():
    try:
        orders = Order.query.all()

        orderData = []

        for order in orders:
            orderedItems = OrderItem.query.filter_by(order_id = order.id).all()
            products = set()
            for item in orderedItems:
                product = Product.query.get(item.product_id)
                products.add(product.name)
            if products:
                orderData.append(list(products))

        print(orderData)

        return json.dumps(orderData)
    except:
        return {'error':'Could not find products'}

@app.route('/api/all-data', methods=['GET'])
def getAllData():
    try:
        orders = Order.query.all()

        orderData = []

        for order in orders:
            orderedItems = OrderItem.query.filter_by(order_id = order.id).all()
            for item in orderedItems:
                product = Product.query.get(item.product_id)
                customer = Customer.query.get(order.customer_id)
                data = {
                    "order_id": order.id,
                    "order_total": order.order_total,
                    "order_date": order.order_date,
                    "payment_method": order.payment_method,
                    "payment_status": order.payment_status,
                    "customer_name": customer.name,
                    "customer_address": customer.address,
                    "product_name": product.name,
                    "product_price": product.price,
                    "ordered_quantity": item.quantity,
                }

                orderData.append(data)

        # print(f"\n\n{orderData}\n\n")
        return orderData
    except:
        return {'error':'Could not find data'}

@app.route('/basket_rule')
def basket_rule():
    return render_template('basket-rule/basket_form.html')

@app.route('/basket_result', methods=['POST'])
def basket_result():
    search_item = request.form['item']
    min_support = float(request.form['min_support'])
    min_confidence = float(request.form['min_confidence'])
    min_lift = float(request.form['min_lift'])
    
    url = "C:/Users/amanm/OneDrive/Desktop/bill/Market_Basket_Optimisation.csv"
    dataset = pd.read_csv(url, encoding='latin1', header=None)
    transactions = []
    for i in range(0, 7501):
        transactions.append([str(dataset.values[i,j]) for j in range(0, 20)])

    rules = apriori(transactions=transactions, min_support=min_support, min_confidence=min_confidence,
                    min_lift=min_lift, min_length=2, max_length=2)
    results = list(rules)

    final = []
    for item in results:
        pair = item[0]
        a = [x for x in pair]
        final.append(a)

    output = []
    for item in final:
        if search_item in item:
            item_index = item.index(search_item)
            if item_index == 1:
                output.append(item[0])
            else:
                output.append(item[1])
    print(results)
    print()
    print(final)
    print()
    print(output)
    return render_template('basket-rule/basket_result.html', search_item=search_item, output=output)


"""
https://www.perplexity.ai/search/how-to-write-T4gKu1wEQaO.51aI2O_RJg?s=c#539e7856-c9dc-49ea-8d3e-a7431c7382e2

OrderID | OrderItemID | ProdID | PName | 

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
   
# 4012888888881881
# 4012001037141112
# - Card Number: 4842 7930 0208 6571
#{'FRUBAN0224988', 'EGGEGG0224512', 'METMEA0224833'}


        