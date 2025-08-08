from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base


Base = declarative_base()


class BarcodeORM(Base):
    __tablename__ = "barcode"
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String)
    order = Column(Integer)
    user_id = Column(Integer, ForeignKey("user.id"))
    stage = Column(Integer)
    is_good = Column(Boolean)
    created_at = Column(DateTime)
    is_sent = Column(Boolean, default=False)
    error_count = Column(Integer, default=0)


class UserORM(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True, autoincrement=True, default=None)
    username = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    first_name = Column(String, default="")
    last_name = Column(String, default="")
    email = Column(String, default="")
    # permissions — можно хранить как строку с JSON, если нужно
    permissions = Column(String, default="[]")
    is_authenticated = Column(Boolean, default=False)
    is_staff = Column(Boolean, default=False)
    is_superuser =Column(Boolean, default=False)


class OrderORM(Base):
    __tablename__ = "device_order"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, default="")
    sort_name = Column(Integer, default=0)
    process_type_id = Column(Integer, nullable=False, default=0)
    # stages = relationship("ProcessStageORM", back_populates="order")  # если нужно


class ProcessTypeORM(Base):
    __tablename__ = 'process_type'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, default="Undefined")
    process_type_id = Column(
        Integer, ForeignKey("process_type.id"), nullable=False, default=0
    )


class SessionORM(Base):
    __tablename__ = 'session'
    id = Column(Integer, primary_key=True, default=1)
    username = Column(String, nullable=False)
    password = Column(String, nullable=False)


class LoginToken(Base):
    __tablename__ = 'user_token'
    id = Column(Integer, primary_key=True)
    token = Column(
        String, ForeignKey("user.id"),
        nullable=True, unique=True
    )
