from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Numeric, NVARCHAR, ForeignKey, Index, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
import uuid
from datetime import datetime, timezone

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    phone_number = Column(Text(), nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))

    jobs_posted = relationship('Job', foreign_keys='Job.posted_by', back_populates='poster')
    jobs_accepted = relationship('Job', foreign_keys='Job.accepted_by', back_populates='accepter')
    chat_sessions = relationship('ChatSession', back_populates='user')
    
    addresses = relationship('Address', back_populates='user')

class Category(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)

    jobs = relationship('Job', back_populates='category')

    __table_args__ = (
        Index('idx_category_name', 'name'),
    )

class Address(Base):
    __tablename__ = 'addresses'
    id = Column(Integer, primary_key=True, autoincrement=True)
    street = Column(NVARCHAR(255), nullable=True)
    city = Column(NVARCHAR(255), nullable=False)
    state = Column(NVARCHAR(255), nullable=False)
    zip_code = Column(NVARCHAR(10), nullable=False)
    country = Column(NVARCHAR(255), nullable=False, default="USA")
    address_index = Column(NVARCHAR(255), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    jobs = relationship('Job', back_populates='address')
    user = relationship('User', back_populates='addresses')

class Job(Base):
    __tablename__ = 'jobs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_description = Column(NVARCHAR(255), nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)
    date_time = Column(DateTime(timezone=True), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    posting_fee = Column(Numeric(10, 2), nullable=True)
    zip_code = Column(NVARCHAR(10), nullable=False)
    posted_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    accepted_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    payment_id = Column(NVARCHAR(255))
    status = Column(NVARCHAR(255), default='pending')
    payment_status = Column(NVARCHAR(255), default='unpaid')
    address_id = Column(Integer, ForeignKey('addresses.id'), nullable=True)
    payment_intent = Column(NVARCHAR(255))
    payment_transfer_id = Column(NVARCHAR(255))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))

    category = relationship('Category', back_populates='jobs')
    poster = relationship('User', foreign_keys=[posted_by], back_populates='jobs_posted')
    accepter = relationship('User', foreign_keys=[accepted_by], back_populates='jobs_accepted')
    address = relationship('Address', back_populates='jobs')
    chat_sessions = relationship('ChatSession', back_populates='job')

    __table_args__ = (
        Index('idx_job_status', 'status'),
        Index('idx_job_date_time', 'date_time'),
        Index('idx_job_category_id', 'category_id'),
    )

class ChatSession(Base):
    __tablename__ = 'chat_sessions'
    id = Column(UNIQUEIDENTIFIER, primary_key=True, default=uuid.uuid4)
    job_id = Column(Integer, ForeignKey('jobs.id'), nullable=True)
    job_type = Column(NVARCHAR(255), nullable=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    job = relationship('Job', back_populates='chat_sessions')
    user = relationship('User', back_populates='chat_sessions')

    __table_args__ = (
        Index('idx_chat_session_id', 'id'),
    )
