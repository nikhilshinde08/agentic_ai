# app/services.py
import asyncio
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import structlog
from collections import defaultdict

# Add src to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(os.path.dirname(current_dir), 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

try:
    from agents.db_agent import AzureReActDatabaseAgent
    from database.connection import DatabaseConnection
except ImportError as e:
    print(f"Warning: Could not import required modules: {e}")
    AzureReActDatabaseAgent = None
    DatabaseConnection = None

logger = structlog.get_logger(__name__)

class DatabaseService:
    """Service for handling database queries using ReAct agent"""
    
    def __init__(self):
        self.agent = None
        self.db_connection = None
        self.schema_cache = None
        self._initialize()
    
    def _initialize(self):
        """Initialize the database service"""
        try:
            if AzureReActDatabaseAgent:
                self.agent = AzureReActDatabaseAgent()
                logger.info("Database service initialized with ReAct agent")
            else:
                logger.error("ReAct agent not available")
                
            if DatabaseConnection:
                self.db_connection = DatabaseConnection()
                logger.info("Database connection initialized")
            else:
                logger.error("Database connection not available")
                
        except Exception as e:
            logger.error(f"Failed to initialize database service: {e}")
            raise
    
    async def test_connection(self) -> bool:
        """Test database connection"""
        try:
            if not self.db_connection:
                return False
            connected, error = await self.db_connection.test_connection()
            return connected
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    async def process_query(self, question: str, session_id: str) -> Dict[str, Any]:
        """Process a natural language query"""
        try:
            if not self.agent:
                raise Exception("Database agent not available")
            
            logger.info(f"Processing query for session {session_id}: {question}")
            
            # Load schema description if available
            schema_description = self._load_schema_description()
            
            # Process with ReAct agent
            result = await self.agent.answer_question(
                question, session_id, schema_description
            )
            
            logger.info(f"Query processed successfully: {result.get('success', False)}")
            return result
            
        except Exception as e:
            logger.error(f"Query processing failed: {e}")
            return {
                "success": False,
                "answer": f"I encountered an error: {str(e)}",
                "query_understanding": question,
                "data": None,
                "sql_generated": None,
                "result_count": 0,
                "metadata": {"error_type": type(e).__name__},
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_schema(self) -> Dict[str, Any]:
        """Get database schema"""
        try:
            if not self.db_connection:
                raise Exception("Database connection not available")
            
            if not self.schema_cache:
                self.schema_cache = await self.db_connection.extract_complete_schema()
            
            return self.schema_cache
        except Exception as e:
            logger.error(f"Schema retrieval failed: {e}")
            raise
    
    def _load_schema_description(self) -> Optional[str]:
        """Load schema description from file"""
        try:
            with open("description.json", 'r', encoding='utf-8') as f:
                return f.read().strip()
        except FileNotFoundError:
            logger.warning("description.json not found")
            return None
        except Exception as e:
            logger.error(f"Error loading description.json: {e}")
            return None
    
    async def close(self):
        """Close database connections"""
        try:
            if self.db_connection:
                await self.db_connection.close()
                logger.info("Database service closed")
        except Exception as e:
            logger.error(f"Error closing database service: {e}")

class ChatService:
    """Service for handling chat interactions"""
    
    def __init__(self):
        self.database_service = DatabaseService()
        self.conversation_memory = defaultdict(list)
    
    async def process_message(
        self, 
        message: str, 
        session_id: str, 
        context: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Process a chat message"""
        try:
            logger.info(f"Processing chat message for session {session_id}: {message}")
            
            # Store user message in conversation memory
            self._add_to_memory(session_id, "user", message)
            
            # Determine if this is a database query or general chat
            if self._is_database_query(message):
                # Process as database query
                result = await self.database_service.process_query(message, session_id)
                
                if result.get("success"):
                    response = self._format_query_response(result)
                else:
                    response = f"I couldn't process that query: {result.get('answer', 'Unknown error')}"
            else:
                # Process as general chat
                response = self._generate_chat_response(message, session_id, context)
            
            # Store assistant response in conversation memory
            self._add_to_memory(session_id, "assistant", response)
            
            logger.info(f"Chat message processed successfully for session {session_id}")
            return response
            
        except Exception as e:
            logger.error(f"Chat processing failed: {e}")
            error_response = f"I'm sorry, I encountered an error: {str(e)}"
            self._add_to_memory(session_id, "assistant", error_response)
            return error_response
    
    def _is_database_query(self, message: str) -> bool:
        """Determine if message is a database query"""
        query_keywords = [
            "how many", "show me", "list", "find", "count", "what are",
            "patients", "conditions", "medications", "procedures", "providers",
            "diagnos", "treatment", "prescription", "hospital", "clinic"
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in query_keywords)
    
    def _format_query_response(self, result: Dict[str, Any]) -> str:
        """Format database query result for chat"""
        response = result.get("answer", "No response available")
        
        # Add additional context if available
        if result.get("result_count", 0) > 0:
            response += f"\n\nI found {result['result_count']} results."
        
        if result.get("sql_generated"):
            response += f"\n\n🔧 Technical details: I used this SQL query to get the answer."
        
        return response
    
    def _generate_chat_response(
        self, 
        message: str, 
        session_id: str, 
        context: Optional[List[Dict[str, Any]]]
    ) -> str:
        """Generate response for general chat"""
        
        # Simple rule-based responses for common chat patterns
        message_lower = message.lower()
        
        if any(greeting in message_lower for greeting in ["hello", "hi", "hey"]):
            return ("Hello! I'm your healthcare database assistant. I can help you explore "
                   "patient data, medical conditions, medications, and more. What would you like to know?")
        
        elif any(word in message_lower for word in ["help", "what can you do"]):
            return ("I can help you with:\n"
                   "• Finding information about patients and their medical history\n"
                   "• Analyzing medical conditions and diagnoses\n"
                   "• Exploring medication data and prescriptions\n"
                   "• Reviewing procedures and treatments\n"
                   "• Getting statistics about your healthcare data\n\n"
                   "Just ask me questions in natural language!")
        
        elif any(word in message_lower for word in ["thanks", "thank you"]):
            return "You're welcome! Is there anything else you'd like to know about your healthcare data?"
        
        elif any(word in message_lower for word in ["bye", "goodbye"]):
            return "Goodbye! Feel free to come back anytime you need help with your healthcare data."
        
        else:
            return ("I'm here to help you explore your healthcare database. Try asking me about "
                   "patients, medical conditions, medications, or any other healthcare data you'd like to analyze.")
    
    def _add_to_memory(self, session_id: str, role: str, content: str):
        """Add message to conversation memory"""
        self.conversation_memory[session_id].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only last 20 messages to prevent memory bloat
        if len(self.conversation_memory[session_id]) > 20:
            self.conversation_memory[session_id] = self.conversation_memory[session_id][-20:]
    
    def get_conversation_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get conversation history for a session"""
        return self.conversation_memory.get(session_id, [])
    
    def clear_conversation(self, session_id: str):
        """Clear conversation history for a session"""
        if session_id in self.conversation_memory:
            del self.conversation_memory[session_id]

class SessionManager:
    """Service for managing user sessions and history"""
    
    def __init__(self):
        self.sessions = {}
        self.query_history = defaultdict(list)
        self.chat_history = defaultdict(list)
        self.stats = {
            "total_sessions": 0,
            "total_queries": 0,
            "total_chat_messages": 0,
            "successful_queries": 0,
            "start_time": datetime.now()
        }
    
    def create_session(self, session_id: str, session_type: str = "query") -> Dict[str, Any]:
        """Create a new session"""
        session_info = {
            "session_id": session_id,
            "session_type": session_type,
            "created_at": datetime.now(),
            "last_activity": datetime.now(),
            "total_interactions": 0,
            "successful_queries": 0
        }
        
        self.sessions[session_id] = session_info
        self.stats["total_sessions"] += 1
        
        logger.info(f"Created new session: {session_id}")
        return session_info
    
    def save_query_response(
        self, 
        session_id: str, 
        question: str, 
        response: Dict[str, Any], 
        processing_time: float
    ):
        """Save query response to session history"""
        try:
            if session_id not in self.sessions:
                self.create_session(session_id, "query")
            
            query_record = {
                "question": question,
                "response": response,
                "processing_time": processing_time,
                "timestamp": datetime.now().isoformat()
            }
            
            self.query_history[session_id].append(query_record)
            
            # Update session info
            self.sessions[session_id]["last_activity"] = datetime.now()
            self.sessions[session_id]["total_interactions"] += 1
            
            if response.get("success"):
                self.sessions[session_id]["successful_queries"] += 1
                self.stats["successful_queries"] += 1
            
            self.stats["total_queries"] += 1
            
            # Save to file in background
            self._save_session_to_file(session_id)
            
        except Exception as e:
            logger.error(f"Failed to save query response: {e}")
    
    def save_chat_message(
        self, 
        session_id: str, 
        user_message: str, 
        assistant_response: str, 
        processing_time: float
    ):
        """Save chat message to session history"""
        try:
            if session_id not in self.sessions:
                self.create_session(session_id, "chat")
            
            chat_record = {
                "user_message": user_message,
                "assistant_response": assistant_response,
                "processing_time": processing_time,
                "timestamp": datetime.now().isoformat()
            }
            
            self.chat_history[session_id].append(chat_record)
            
            # Update session info
            self.sessions[session_id]["last_activity"] = datetime.now()
            self.sessions[session_id]["total_interactions"] += 1
            
            self.stats["total_chat_messages"] += 1
            
            # Save to file in background
            self._save_session_to_file(session_id)
            
        except Exception as e:
            logger.error(f"Failed to save chat message: {e}")
    
    def get_session_history(self, session_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get query history for a session"""
        return self.query_history.get(session_id)
    
    def get_chat_history(self, session_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get chat history for a session"""
        return self.chat_history.get(session_id)
    
    def get_recent_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent sessions"""
        sessions = list(self.sessions.values())
        sessions.sort(key=lambda x: x["last_activity"], reverse=True)
        return sessions[:limit]
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session and its history"""
        try:
            if session_id in self.sessions:
                del self.sessions[session_id]
            
            if session_id in self.query_history:
                del self.query_history[session_id]
            
            if session_id in self.chat_history:
                del self.chat_history[session_id]
            
            # Delete session file
            try:
                session_file = f"sessions/{session_id}.json"
                if os.path.exists(session_file):
                    os.remove(session_file)
            except Exception as e:
                logger.warning(f"Could not delete session file: {e}")
            
            logger.info(f"Deleted session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete session: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get API usage statistics"""
        uptime = (datetime.now() - self.stats["start_time"]).total_seconds()
        
        # Calculate average response time
        total_processing_time = 0
        total_requests = 0
        
        for session_queries in self.query_history.values():
            for query in session_queries:
                total_processing_time += query.get("processing_time", 0)
                total_requests += 1
        
        for session_chats in self.chat_history.values():
            for chat in session_chats:
                total_processing_time += chat.get("processing_time", 0)
                total_requests += 1
        
        avg_response_time = (total_processing_time / total_requests) if total_requests > 0 else 0
        
        return {
            "total_sessions": self.stats["total_sessions"],
            "total_queries": self.stats["total_queries"],
            "total_chat_messages": self.stats["total_chat_messages"],
            "successful_queries": self.stats["successful_queries"],
            "average_response_time": round(avg_response_time, 3),
            "uptime_seconds": round(uptime, 1)
        }
    
    def _save_session_to_file(self, session_id: str):
        """Save session data to file"""
        try:
            os.makedirs("sessions", exist_ok=True)
            
            session_data = {
                "session_info": self.sessions.get(session_id, {}),
                "query_history": self.query_history.get(session_id, []),
                "chat_history": self.chat_history.get(session_id, [])
            }
            
            session_file = f"sessions/{session_id}.json"
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, default=str, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Failed to save session to file: {e}")