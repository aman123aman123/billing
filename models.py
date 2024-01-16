# https://www.youtube.com/playlist?list=PLXmMXHVSvS-BlLA5beNJojJLlpE0PJgCW

from sqlalchemy import Column, ForeignKey, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

class Customer(Base):
    __tablename__ = 'customers'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    phone = Column(Integer, nullable=False)

    orders = relationship("Order", backref="customers")

    def __repr__(self) -> str:
        return f"User: {self.name}"

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)
    barcode = Column(String, nullable=False)

    def __repr__(self) -> str:
        return f"{self.barcode} - {self.productname}"

class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    order_date = Column(DateTime, nullable=False, default=datetime.now())
    order_total = Column(Integer, nullable=False)
    
    customer_id = Column(Integer, ForeignKey("customers.id"))

class OrderItem(Base):
    __tablename__ = 'order_items'
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer, nullable=False)
    price_per_quantity = Column(Integer, nullable=False)
