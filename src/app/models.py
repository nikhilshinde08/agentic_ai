# app/models.py
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

class AgentType(str, Enum):
    REACT = "react"
    CHAT = "chat"

class QueryRequest(BaseModel):
    """Request model for database queries"""
    question: str = Field(..., description="Natural language question about the database")
    session_id: Optional[str] = Field(None, description="Session identifier for tracking")
    agent_type: AgentType = Field(AgentType.REACT, description="Type of agent to use")
    include_metadata: bool = Field(True, description="Whether to include detailed metadata")
    
    class Config:
        schema_extra = {
            "example": {
                "question": "How many patients do we have with diabetes?",
                "session_id": "session_123",
                "agent_type": "react",
                "include_metadata": True
            }
        }

class QueryResponse(BaseModel):
    """Response model for database queries"""
    success: bool = Field(..., description="Whether the query was successful")
    message: str = Field(..., description="Human-readable response message")
    query_understanding: str = Field(..., description="How the AI interpreted the question")
    sql_query: Optional[str] = Field(None, description="Generated SQL query")
    result_count: int = Field(0, description="Number of results returned")
    results: List[Dict[str, Any]] = Field(default_factory=list, description="Query results")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    session_id: str = Field(..., description="Session identifier")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Found 150 patients with diabetes",
                "query_understanding": "Find count of patients diagnosed with diabetes",
                "sql_query": "SELECT COUNT(*) FROM patients p JOIN conditions c ON p.id = c.patient WHERE c.description ILIKE '%diabetes%'",
                "result_count": 1,
                "results": [{"count": 150}],
                "metadata": {"processing_time_seconds": 2.5, "tables_used": ["patients", "conditions"]},
                "session_id": "session_123",
                "timestamp": "2024-01-01T12:00:00"
            }
        }

class ChatMessage(BaseModel):
    """Individual chat message"""
    role: str = Field(..., description="Message role: user or assistant")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.now, description="Message timestamp")

class ChatRequest(BaseModel):
    """Request model for chat messages"""
    message: str = Field(..., description="User message")
    session_id: Optional[str] = Field(None, description="Session identifier for conversation tracking")
    context: Optional[List[ChatMessage]] = Field(default_factory=list, description="Previous conversation context")
    
    class Config:
        schema_extra = {
            "example": {
                "message": "Tell me about the patients in our database",
                "session_id": "chat_123",
                "context": []
            }
        }

class ChatResponse(BaseModel):
    """Response model for chat messages"""
    message: str = Field(..., description="Assistant response message")
    session_id: str = Field(..., description="Session identifier")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        schema_extra = {
            "example": {
                "message": "I can help you explore your healthcare database. We have patient records, medical conditions, medications, and more. What would you like to know?",
                "session_id": "chat_123",
                "timestamp": "2024-01-01T12:00:00",
                "metadata": {"processing_time_seconds": 1.2}
            }
        }

class SessionInfo(BaseModel):
    """Session information model"""
    session_id: str = Field(..., description="Session identifier")
    session_type: str = Field(..., description="Type of session: query or chat")
    created_at: datetime = Field(..., description="Session creation time")
    last_activity: datetime = Field(..., description="Last activity timestamp")
    total_interactions: int = Field(0, description="Total number of interactions")
    successful_queries: int = Field(0, description="Number of successful queries")

class HealthCheck(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="Service status: healthy or unhealthy")
    timestamp: datetime = Field(default_factory=datetime.now, description="Check timestamp")
    database_connected: bool = Field(..., description="Database connection status")
    version: str = Field(..., description="API version")
    error: Optional[str] = Field(None, description="Error message if unhealthy")

class AgentStats(BaseModel):
    """Agent statistics model"""
    total_sessions: int = Field(0, description="Total number of sessions")
    total_queries: int = Field(0, description="Total number of queries processed")
    total_chat_messages: int = Field(0, description="Total number of chat messages")
    successful_queries: int = Field(0, description="Number of successful queries")
    average_response_time: float = Field(0.0, description="Average response time in seconds")
    uptime_seconds: float = Field(0.0, description="Service uptime in seconds")
    
class ErrorResponse(BaseModel):
    """Standard error response model"""
    error: str = Field(..., description="Error message")
    error_type: str = Field(..., description="Type of error")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")
    session_id: Optional[str] = Field(None, description="Session identifier if applicable")

class SchemaTable(BaseModel):
    """Database table schema model"""
    name: str = Field(..., description="Table name")
    schema: str = Field(..., description="Schema name")
    columns: List[Dict[str, Any]] = Field(..., description="Table columns")
    relationships: List[Dict[str, Any]] = Field(default_factory=list, description="Table relationships")

class SchemaResponse(BaseModel):
    """Database schema response model"""
    tables: List[SchemaTable] = Field(..., description="Database tables")
    total_tables: int = Field(..., description="Total number of tables")
    relationships: List[Dict[str, Any]] = Field(default_factory=list, description="All relationships")

class StreamStatus(BaseModel):
    """Streaming response status model"""
    status: str = Field(..., description="Current status")
    session_id: str = Field(..., description="Session identifier")
    progress: Optional[int] = Field(None, description="Progress percentage")
    message: Optional[str] = Field(None, description="Status message")

class BulkQueryRequest(BaseModel):
    """Request model for bulk queries"""
    questions: List[str] = Field(..., description="List of questions to process")
    session_id: Optional[str] = Field(None, description="Session identifier")
    parallel: bool = Field(False, description="Whether to process queries in parallel")

class BulkQueryResponse(BaseModel):
    """Response model for bulk queries"""
    results: List[QueryResponse] = Field(..., description="Query results")
    session_id: str = Field(..., description="Session identifier")
    total_queries: int = Field(..., description="Total number of queries processed")
    successful_queries: int = Field(..., description="Number of successful queries")
    total_processing_time: float = Field(..., description="Total processing time in seconds")