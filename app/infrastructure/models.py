"""业务 ORM 模型共用的基类。"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """业务模型继承此类，并在 migrations/env.py 中显式导入。"""
