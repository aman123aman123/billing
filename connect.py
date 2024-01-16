# SQL Alchemy
# https://www.youtube.com/watch?v=XWtj4zLl_tg
# Relationships
# https://www.youtube.com/watch?v=cc0xt9uuKQo
# https://github.com/jod35/sqlalchemy_one_to_many_relationship/blob/main/main.py

from sqlalchemy import create_engine, text

engine = create_engine("sqlite:///sample.db")

with engine.connect() as connection:
    result = connection.execute(text('Select "Text"'))
    print(result.all())