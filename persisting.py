# https://docs.sqlalchemy.org/en/14/orm/basic_relationships.html

# https://github.com/jod35/SQLAlchemy-2.0-ORM/blob/main/persisting.py

# https://thepythoncode.com/article/making-a-barcode-scanner-in-python

from models import User, Product, Order, OrderItem
from main import session
from datetime import datetime

aman = User(
    name = 'aman',
    address="Kelshi",
    phone= 123,
)

arshad = User(
    name = 'arshad',
    address="dapoli",
    phone= 456,
)

arbaz = User(
    name = 'arbaz',
    address="bahiravli",
    phone= 789,
)

oats = Product(
    name="oats",
    price=12,
    quantity=1,
    barcode="ABZ123"
)

sugar = Product(
    name="sugar",
    price=20,
    quantity=1,
    barcode="DBA243"
)

milk = Product(
    name="milk",
    price=28,
    quantity=1,
    barcode="SDG682"
)

# session.add_all([aman, arshad, arbaz, oats, sugar, milk])


aman = session.query(User).filter_by(name="aman").first()
order1 = Order(
    order_total = 120,
    user_id=aman.id
)



order1 = session.query(Order).first()
oats = session.query(Product).filter_by(name="oats").first()

order_item1 = OrderItem(
    order_id=order1.id,
    product_id=oats.id,
    quantity=10,
    price_per_quantity=oats.price,
)

session.add_all([order_item1])


session.commit()