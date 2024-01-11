from sqlalchemy import Column, ForeignKey, Integer, String, Float, Table
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

order_products = Table(
    "order_products",
    Base.metadata,
    Column("order_id", ForeignKey("orders.id")),
    Column("product_id", ForeignKey("products.id")),
)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    phone = Column(Integer, nullable=False)

    order_user = relationship("Order", back_populates="user")

    def __repr__(self) -> str:
        return f"User: {self.name}"

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)
    barcode = Column(String, nullable=False)

    order_product = relationship("Order", back_populates="")

    def __repr__(self) -> str:
        return f"{self.barcode} - {self.productname}"

class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="order_user")

    order_products = relationship("Child", secondary=order_products)
