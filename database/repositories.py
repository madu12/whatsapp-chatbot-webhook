import datetime
from sqlalchemy.orm import Session
from database.models import User, Job, Category, ChatSession
from database.db_session import create_session
from sqlalchemy.exc import SQLAlchemyError


class UserRepository:
    @staticmethod
    def get_user_by_phone_number(phone_number: str):
        """
        Retrieve a user by their phone number.
        """
        session = create_session()
        return session.query(User).filter(User.phone_number == phone_number).first()

    @staticmethod
    def create_user(name: str, phone_number: str):
        """
        Create a new user with the given name and phone number.
        """
        session = create_session()
        user = User(name=name, phone_number=phone_number)
        session.add(user)
        session.commit()
        session.refresh(user)
        return user
    
class ChatSessionRepository:
    @staticmethod
    def create_chat_session(chat_session_id, job_type, user_id):
        """
        Create a new chat session.
        """
        session = create_session()
        new_session = ChatSession(id=chat_session_id, job_type=job_type, user_id=user_id)
        session.add(new_session)
        session.commit()
        return new_session

    @staticmethod
    def get_latest_chat_session_by_user(user_id):
        """
        Retrieve the latest chat session for a user.
        """
        session = create_session()
        return session.query(ChatSession).filter_by(user_id=user_id).order_by(ChatSession.created_at.desc()).first()
    
    @staticmethod
    def update_chat_session_job_id(chat_session_id: str, job_id: int):
        """
        Update the job ID associated with a chat session.
        """
        session = create_session()
        chat_session = session.query(ChatSession).filter(ChatSession.id == chat_session_id).first()
        if chat_session:
            chat_session.job_id = job_id
            session.commit()
            session.refresh(chat_session)
        return chat_session

class CategoryRepository:
    @staticmethod
    def get_category_by_name(category_name):
        """
        Retrieve a category by its name.
        """
        session = create_session()
        return session.query(Category).filter_by(name=category_name).first()

class JobRepository:
    @staticmethod
    def create_job(job_description, category_id, date_time, amount, posting_fee, zip_code, posted_by):
        """
        Create a new job posting.
        """
        session = create_session()
        job = Job(
            job_description=job_description,
            category_id=category_id,
            date_time=date_time,
            amount=amount,
            posting_fee=posting_fee,
            zip_code=zip_code,
            posted_by=posted_by,
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        return job

    @staticmethod
    def get_job_by_id(job_id):
        """
        Retrieve a job by its ID.
        """
        session = create_session()
        return session.query(Job).filter_by(id=job_id).first()
    
    @staticmethod
    def update_job(job_id, update_data):
        """
        Update a job with the given data.
        """
        session = create_session()
        job = session.query(Job).filter_by(id=job_id).first()
        if not job:
            return {"error": "Job not found"}

        for key, value in update_data.items():
            setattr(job, key, value)

        session.commit()
        session.refresh(job)
        return job
