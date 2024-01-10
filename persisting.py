# https://docs.sqlalchemy.org/en/14/orm/basic_relationships.html

from models import User
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