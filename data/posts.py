import datetime

import sqlalchemy
from sqlalchemy import orm

from .db_session import SqlAlchemyBase


class Posts(SqlAlchemyBase):
    """Класс для создания записей о постах в БД"""
    __tablename__ = 'posts'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    title = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    content = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    created_date = sqlalchemy.Column(sqlalchemy.String,
                                     default=datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
    is_private = sqlalchemy.Column(sqlalchemy.Boolean, default=True)

    user_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("users.id"))
    user = orm.relation('User')
