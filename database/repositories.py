import datetime
from sqlalchemy.orm import Session
from database.models import User, Job, Category, Address, ChatSession
from database.db_session import create_session

class UserRepository:
    @staticmethod
    def get_user_by_phone_number(phone_number: str):
        session = create_session()
        return session.query(User).filter(User.phone_number == phone_number).first()

    @staticmethod
    def create_user(name: str, phone_number: str):
        session = create_session()
        user = User(name=name, phone_number=phone_number)
        session.add(user)
        session.commit()
        session.refresh(user)
        return user
    
class ChatSessionRepository:
    @staticmethod
    def create_chat_session(chat_session_id, job_type, user_id):
        session = create_session()
        new_session = ChatSession(id=chat_session_id, job_type=job_type, user_id=user_id)
        session.add(new_session)
        session.commit()
        return new_session

    @staticmethod
    def get_latest_chat_session_by_user(user_id):
        session = create_session()
        return session.query(ChatSession).filter_by(user_id=user_id).order_by(ChatSession.created_at.desc()).first()
