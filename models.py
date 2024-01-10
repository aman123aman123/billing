from sqlalchemy import Column, ForeignKey, Integer, String, Float
from sqlalchemy.orm import DeclarativeBase, relationship, declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

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