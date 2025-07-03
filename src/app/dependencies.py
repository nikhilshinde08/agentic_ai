# app/dependencies.py
from fastapi import Depends, HTTPException
from app.services import DatabaseService, ChatService, SessionManager
import structlog

logger = structlog.get_logger(__name__)

# Global service instances
_database_service = None
_chat_service = None
_session_manager = None

def get_database_service() -> DatabaseService:
    """Dependency to get database service instance"""
    global _database_service
    
    if _database_service is None:
        try:
            _database_service = DatabaseService()
        except Exception as e:
            logger.error(f"Failed to initialize database service: {e}")
            raise HTTPException(
                status_code=503,
                detail="Database service unavailable"
            )
    
    return _database_service

def get_chat_service() -> ChatService:
    """Dependency to get chat service instance"""
    global _chat_service
    
    if _chat_service is None:
        try:
            _chat_service = ChatService()
        except Exception as e:
            logger.error(f"Failed to initialize chat service: {e}")
            raise HTTPException(
                status_code=503,
                detail="Chat service unavailable"
            )
    
    return _chat_service

def get_session_manager() -> SessionManager:
    """Dependency to get session manager instance"""
    global _session_manager
    
    if _session_manager is None:
        try:
            _session_manager = SessionManager()
        except Exception as e:
            logger.error(f"Failed to initialize session manager: {e}")
            raise HTTPException(
                status_code=503,
                detail="Session manager unavailable"
            )
    
    return _session_manager

async def verify_database_connection(
    db_service: DatabaseService = Depends(get_database_service)
):
    """Dependency to verify database connection"""
    if not await db_service.test_connection():
        raise HTTPException(
            status_code=503,
            detail="Database connection unavailable"
        )
    return db_service

def validate_session_id(session_id: str) -> str:
    """Validate session ID format"""
    if not session_id or len(session_id) < 3:
        raise HTTPException(
            status_code=400,
            detail="Invalid session ID"
        )
    return session_id

def validate_query_request(question: str) -> str:
    """Validate query request"""
    if not question or len(question.strip()) < 3:
        raise HTTPException(
            status_code=400,
            detail="Question must be at least 3 characters long"
        )
    
    if len(question) > 1000:
        raise HTTPException(
            status_code=400,
            detail="Question too long (max 1000 characters)"
        )
    
    return question.strip()

def validate_chat_message(message: str) -> str:
    """Validate chat message"""
    if not message or len(message.strip()) < 1:
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty"
        )
    
    if len(message) > 2000:
        raise HTTPException(
            status_code=400,
            detail="Message too long (max 2000 characters)"
        )
    
    return message.strip()