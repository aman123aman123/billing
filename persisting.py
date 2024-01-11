# https://docs.sqlalchemy.org/en/14/orm/basic_relationships.html

# https://github.com/jod35/SQLAlchemy-2.0-ORM/blob/main/persisting.py

from models import User, Product, Order
from main import session

user1 = User(
    name = 'aman',
)

paul = User(
    name = 'arshad',
)

cathy = User(
    name = 'arbaz',
)

session.add_all([user1,paul,cathy])

session.commit()