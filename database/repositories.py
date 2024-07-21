import datetime
from sqlalchemy import and_
from sqlalchemy.orm import Session
from database.models import User, Job, Category, ChatSession, Address
from database.db_session import create_session
from sqlalchemy.exc import SQLAlchemyError
from utils.general_utils import GeneralUtils


class UserRepository:
    @staticmethod
    async def get_user_by_phone_number(phone_number: str):
        """
        Retrieve a user by their phone number.
        
        Args:
            phone_number (str): The phone number of the user.
        
        Returns:
            User: The user object if found, else None.
        """
        try:
            session = create_session()
            return session.query(User).filter(User.phone_number == phone_number).first()
        except SQLAlchemyError as e:
            print(f"Error retrieving user by phone number: {e}")
            return None

    @staticmethod
    async def create_user(name: str, phone_number: str):
        """
        Create a new user with the given name and phone number.
        
        Args:
            name (str): The name of the user.
            phone_number (str): The phone number of the user.
        
        Returns:
            User: The created user object if successful, else None.
        """
        try:
            session = create_session()
            user = User(name=name, phone_number=phone_number)
            session.add(user)
            session.commit()
            session.refresh(user)
            return user
        except SQLAlchemyError as e:
            print(f"Error creating user: {e}")
            session.rollback()
            return None


class ChatSessionRepository:
    @staticmethod
    async def create_chat_session(chat_session_id, job_type, user_id):
        """
        Create a new chat session.
        
        Args:
            chat_session_id (str): The ID of the chat session.
            job_type (str): The type of job associated with the chat session.
            user_id (int): The ID of the user associated with the chat session.
        
        Returns:
            ChatSession: The created chat session object if successful, else None.
        """
        try:
            session = create_session()
            new_session = ChatSession(id=chat_session_id, job_type=job_type, user_id=user_id)
            session.add(new_session)
            session.commit()
            return new_session
        except SQLAlchemyError as e:
            print(f"Error creating chat session: {e}")
            session.rollback()
            return None

    @staticmethod
    async def get_latest_chat_session_by_user(user_id):
        """
        Retrieve the latest chat session for a user.
        
        Args:
            user_id (int): The ID of the user.
        
        Returns:
            ChatSession: The latest chat session object if found, else None.
        """
        try:
            session = create_session()
            return session.query(ChatSession).filter_by(user_id=user_id).order_by(ChatSession.created_at.desc()).first()
        except SQLAlchemyError as e:
            print(f"Error retrieving latest chat session: {e}")
            return None

    @staticmethod
    async def update_chat_session_job_id(chat_session_id: str, job_id: int):
        """
        Update the job ID associated with a chat session.
        
        Args:
            chat_session_id (str): The ID of the chat session.
            job_id (int): The new job ID to associate with the chat session.
        
        Returns:
            ChatSession: The updated chat session object if successful, else None.
        """
        try:
            session = create_session()
            chat_session = session.query(ChatSession).filter(ChatSession.id == chat_session_id).first()
            if chat_session:
                chat_session.job_id = job_id
                session.commit()
                session.refresh(chat_session)
            return chat_session
        except SQLAlchemyError as e:
            print(f"Error updating chat session job ID: {e}")
            session.rollback()
            return None


class CategoryRepository:
    @staticmethod
    async def get_category_by_name(category_name):
        """
        Retrieve a category by its name.
        
        Args:
            category_name (str): The name of the category.
        
        Returns:
            Category: The category object if found, else None.
        """
        try:
            session = create_session()
            return session.query(Category).filter_by(name=category_name).first()
        except SQLAlchemyError as e:
            print(f"Error retrieving category by name: {e}")
            return None


class JobRepository:
    @staticmethod
    async def create_job(job_description, category_id, date_time, amount, posting_fee, zip_code, posted_by):
        """
        Create a new job posting.
        
        Args:
            job_description (str): The description of the job.
            category_id (int): The ID of the category for the job.
            date_time (datetime): The date and time of the job.
            amount (float): The payment amount for the job.
            posting_fee (float): The fee for posting the job.
            zip_code (str): The ZIP code where the job is located.
            posted_by (int): The ID of the user who posted the job.
        
        Returns:
            Job: The created job object if successful, else None.
        """
        try:
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
        except SQLAlchemyError as e:
            print(f"Error creating job: {e}")
            session.rollback()
            return None

    @staticmethod
    async def get_job_by_id(job_id):
        """
        Retrieve a job by its ID.
        
        Args:
            job_id (int): The ID of the job.
        
        Returns:
            Job: The job object if found, else None.
        """
        try:
            session = create_session()
            return session.query(Job).filter_by(id=job_id).first()
        except SQLAlchemyError as e:
            print(f"Error retrieving job by ID: {e}")
            return None
    
    @staticmethod
    async def get_job_by_payment_id(payment_id):
        """
        Retrieve a job by its Payment ID.
        
        Args:
            payment_id (int): The payment ID associated with the job.
        
        Returns:
            Job: The job object if found, else None.
        """
        try:
            session = create_session()
            return session.query(Job).filter_by(payment_id=payment_id).first()
        except SQLAlchemyError as e:
            print(f"Error retrieving job by Payment ID: {e}")
            return None

    @staticmethod
    async def update_job(where, update_data):
        """
        Update a job based on custom criteria.
        
        Args:
            where (dict): A dictionary specifying the filter criteria.
            update_data (dict): A dictionary specifying the fields to update.
        
        Returns:
            Job: The updated job object if successful, else None.
        """
        try:
            session = create_session()
            query = session.query(Job)
            
            # Apply filters from the 'where' dictionary
            for key, value in where.items():
                query = query.filter(getattr(Job, key) == value)
            
            job = query.first()
            if not job:
                return None

            # Update fields from the 'update_data' dictionary
            for key, value in update_data.items():
                setattr(job, key, value)

            session.commit()
            session.refresh(job)
            return job
        except SQLAlchemyError as e:
            print(f"Error updating job: {e}")
            session.rollback()
            return None

class AddressRepository:
    @staticmethod
    async def register_address(address_data, user_id):
        """
        Register an address for a user.
        
        Args:
            address_data (dict): Dictionary containing address details.
            user_id (int): The ID of the user.
        
        Returns:
            dict: A dictionary containing the registration status and address data.
        """
        try:
            session = create_session()
            utils = GeneralUtils()
            address_index = utils.get_address_index(address_data)

            existing_address = session.query(Address).filter_by(address_index=address_index, user_id=user_id).first()

            if not existing_address:
                new_address = Address(
                    user_id=user_id,
                    street=address_data.get('street', ''),
                    city=address_data.get('city', ''),
                    zip_code=address_data.get('zip_code', ''),
                    state=address_data.get('state', ''),
                    country=address_data.get('country', 'USA'),
                    address_index=address_index
                )
                session.add(new_address)
                session.commit()
                session.refresh(new_address)
                return {"existing_address": False, "address_data": new_address}
            else:
                return {"existing_address": True, "address_data": existing_address}
        except SQLAlchemyError as e:
            print(f"Error registering user address: {e}")
            session.rollback()
            raise e
