# https://www.youtube.com/playlist?list=PLXmMXHVSvS-BlLA5beNJojJLlpE0PJgCW

from app import db
from datetime import datetime

# db = SQLAlchemy()

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
        return f"{self.barcode} - {self.productname}"

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
