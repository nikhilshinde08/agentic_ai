# app/main.py
import sys
import os
# Ensure src is in PYTHONPATH for module resolution
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.abspath(os.path.join(current_dir, '..', '..'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid
import structlog

from src.app.models import (
    QueryRequest, QueryResponse, ChatMessage, ChatRequest, 
    ChatResponse, SessionInfo, HealthCheck, AgentStats
)
from app.services import DatabaseService, ChatService, SessionManager
from src.app.dependencies import get_database_service, get_chat_service, get_session_manager

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Healthcare Database Assistant API",
    description="AI-powered healthcare database query assistant with ReAct agent and chatbot capabilities",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_dir = os.path.join(current_dir, "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Global variables for services
_database_service = None
_chat_service = None
_session_manager = None

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global _database_service, _chat_service, _session_manager
    
    logger.info("Starting Healthcare Database Assistant API...")
    
    try:
        # Initialize services
        _database_service = DatabaseService()
        _chat_service = ChatService()
        _session_manager = SessionManager()
        
        # Test database connection
        await _database_service.test_connection()
        
        logger.info("API startup completed successfully")
    except Exception as e:
        logger.error(f"Failed to start API: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Healthcare Database Assistant API...")
    
    if _database_service:
        await _database_service.close()
    
    logger.info("API shutdown completed")

# Health Check Endpoints
@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    try:
        db_service = get_database_service()
        db_status = await db_service.test_connection()
        
        return HealthCheck(
            status="healthy" if db_status else "unhealthy",
            timestamp=datetime.now(),
            database_connected=db_status,
            version="1.0.0"
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthCheck(
            status="unhealthy",
            timestamp=datetime.now(),
            database_connected=False,
            version="1.0.0",
            error=str(e)
        )

@app.get("/stats", response_model=AgentStats)
async def get_stats(session_manager: SessionManager = Depends(get_session_manager)):
    """Get API usage statistics"""
    return session_manager.get_stats()

# ReAct Agent Endpoints
@app.post("/query", response_model=QueryResponse)
async def query_database(
    request: QueryRequest,
    background_tasks: BackgroundTasks,
    db_service: DatabaseService = Depends(get_database_service),
    session_manager: SessionManager = Depends(get_session_manager)
):
    """Process database query using ReAct agent"""
    try:
        logger.info(f"Processing query: {request.question}")
        
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Process query
        start_time = datetime.now()
        result = await db_service.process_query(request.question, session_id)
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Create response
        response = QueryResponse(
            success=result.get("success", False),
            message=result.get("answer", "No response"),
            query_understanding=result.get("query_understanding", request.question),
            sql_query=result.get("sql_generated"),
            result_count=result.get("result_count", 0),
            results=result.get("data", []),
            metadata={
                **result.get("metadata", {}),
                "processing_time_seconds": processing_time,
                "session_id": session_id,
                "api_version": "1.0.0"
            },
            session_id=session_id,
            timestamp=datetime.now()
        )
        
        # Save session data in background
        background_tasks.add_task(
            session_manager.save_query_response,
            session_id, request.question, response.dict(), processing_time
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Query processing failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Query processing failed: {str(e)}"
        )

@app.get("/query/history/{session_id}")
async def get_query_history(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """Get query history for a session"""
    try:
        history = session_manager.get_session_history(session_id)
        if not history:
            raise HTTPException(status_code=404, detail="Session not found")
        return {"session_id": session_id, "history": history}
    except Exception as e:
        logger.error(f"Failed to get query history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Chat Endpoints
@app.post("/chat", response_model=ChatResponse)
async def chat_with_bot(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    chat_service: ChatService = Depends(get_chat_service),
    session_manager: SessionManager = Depends(get_session_manager)
):
    """Chat with the healthcare database assistant"""
    try:
        logger.info(f"Processing chat message: {request.message}")
        
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Process chat message
        start_time = datetime.now()
        response_text = await chat_service.process_message(
            request.message, session_id, request.context
        )
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Create response
        response = ChatResponse(
            message=response_text,
            session_id=session_id,
            timestamp=datetime.now(),
            metadata={
                "processing_time_seconds": processing_time,
                "api_version": "1.0.0"
            }
        )
        
        # Save chat data in background
        background_tasks.add_task(
            session_manager.save_chat_message,
            session_id, request.message, response_text, processing_time
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Chat processing failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Chat processing failed: {str(e)}"
        )

@app.get("/chat/history/{session_id}")
async def get_chat_history(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """Get chat history for a session"""
    try:
        history = session_manager.get_chat_history(session_id)
        if not history:
            raise HTTPException(status_code=404, detail="Session not found")
        return {"session_id": session_id, "history": history}
    except Exception as e:
        logger.error(f"Failed to get chat history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Database Schema Endpoints
@app.get("/schema")
async def get_database_schema(
    db_service: DatabaseService = Depends(get_database_service)
):
    """Get database schema information"""
    try:
        schema = await db_service.get_schema()
        return {"schema": schema}
    except Exception as e:
        logger.error(f"Failed to get schema: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/schema/tables")
async def get_tables(
    db_service: DatabaseService = Depends(get_database_service)
):
    """Get list of database tables"""
    try:
        schema = await db_service.get_schema()
        tables = [
            {
                "name": table_info["name"],
                "columns": len(table_info.get("columns", [])),
                "schema": table_info.get("schema", "public")
            }
            for table_info in schema.get("tables", {}).values()
        ]
        return {"tables": tables}
    except Exception as e:
        logger.error(f"Failed to get tables: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Session Management Endpoints
@app.get("/sessions", response_model=List[SessionInfo])
async def get_sessions(
    limit: int = 50,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """Get recent sessions"""
    try:
        sessions = session_manager.get_recent_sessions(limit)
        return sessions
    except Exception as e:
        logger.error(f"Failed to get sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """Delete a session and its history"""
    try:
        success = session_manager.delete_session(session_id)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        return {"message": f"Session {session_id} deleted successfully"}
    except Exception as e:
        logger.error(f"Failed to delete session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Streaming Endpoints
@app.post("/query/stream")
async def stream_query_response(
    request: QueryRequest,
    db_service: DatabaseService = Depends(get_database_service)
):
    """Stream query response for real-time updates"""
    async def generate_stream():
        try:
            session_id = request.session_id or str(uuid.uuid4())
            
            # Send initial status
            yield f"data: {json.dumps({'status': 'processing', 'session_id': session_id})}\n\n"
            
            # Process query
            result = await db_service.process_query(request.question, session_id)
            
            # Send final result
            yield f"data: {json.dumps(result)}\n\n"
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            error_response = {
                "status": "error",
                "error": str(e),
                "session_id": session_id
            }
            yield f"data: {json.dumps(error_response)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )

# Web Interface
@app.get("/", response_class=HTMLResponse)
async def get_web_interface():
    """Serve web interface"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Healthcare Database Assistant</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; }
            .header { text-align: center; margin-bottom: 30px; }
            .header h1 { color: #2c3e50; margin-bottom: 10px; }
            .header p { color: #7f8c8d; }
            .tabs { display: flex; margin-bottom: 20px; }
            .tab { padding: 10px 20px; margin-right: 10px; background: #3498db; color: white; 
                   cursor: pointer; border-radius: 5px; }
            .tab.active { background: #2980b9; }
            .content { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .input-group { margin-bottom: 15px; }
            .input-group label { display: block; margin-bottom: 5px; font-weight: bold; }
            .input-group input, .input-group textarea { width: 100%; padding: 10px; border: 1px solid #ddd; 
                                                       border-radius: 4px; box-sizing: border-box; }
            .input-group textarea { height: 100px; resize: vertical; }
            .btn { background: #27ae60; color: white; padding: 12px 24px; border: none; 
                   border-radius: 4px; cursor: pointer; font-size: 16px; }
            .btn:hover { background: #229954; }
            .response { margin-top: 20px; padding: 15px; background: #f8f9fa; 
                       border-radius: 4px; border-left: 4px solid #27ae60; }
            .error { border-left-color: #e74c3c; background: #fdf2f2; }
            .loading { text-align: center; margin: 20px 0; }
            .example { background: #e8f4f8; padding: 10px; margin: 10px 0; border-radius: 4px; }
            .example-title { font-weight: bold; margin-bottom: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏥 Healthcare Database Assistant</h1>
                <p>AI-powered natural language database queries for healthcare data</p>
            </div>
            
            <div class="tabs">
                <div class="tab active" onclick="showTab('query')">Database Query</div>
                <div class="tab" onclick="showTab('chat')">Chat Assistant</div>
                <div class="tab" onclick="showTab('schema')">Database Schema</div>
            </div>
            
            <div id="query-tab" class="content">
                <h2>Database Query</h2>
                <p>Ask questions about your healthcare data in natural language.</p>
                
                <div class="example">
                    <div class="example-title">Example Questions:</div>
                    • How many patients do we have?<br>
                    • Show me patients with diabetes<br>
                    • What are the most common medical conditions?<br>
                    • List medications prescribed for hypertension
                </div>
                
                <form onsubmit="submitQuery(event)">
                    <div class="input-group">
                        <label for="question">Your Question:</label>
                        <textarea id="question" placeholder="Enter your question about the healthcare data..." required></textarea>
                    </div>
                    <button type="submit" class="btn">Submit Query</button>
                </form>
                
                <div id="query-loading" class="loading" style="display: none;">
                    Processing your query...
                </div>
                
                <div id="query-response"></div>
            </div>
            
            <div id="chat-tab" class="content" style="display: none;">
                <h2>Chat Assistant</h2>
                <p>Have a conversation with the AI assistant about your healthcare data.</p>
                
                <div id="chat-history" style="height: 400px; overflow-y: auto; border: 1px solid #ddd; 
                                              padding: 10px; margin-bottom: 15px; background: #fafafa;"></div>
                
                <form onsubmit="sendChatMessage(event)">
                    <div class="input-group">
                        <label for="chat-message">Message:</label>
                        <input type="text" id="chat-message" placeholder="Type your message..." required>
                    </div>
                    <button type="submit" class="btn">Send Message</button>
                </form>
            </div>
            
            <div id="schema-tab" class="content" style="display: none;">
                <h2>Database Schema</h2>
                <p>Explore the structure of your healthcare database.</p>
                
                <button onclick="loadSchema()" class="btn">Load Schema</button>
                
                <div id="schema-loading" class="loading" style="display: none;">
                    Loading database schema...
                </div>
                
                <div id="schema-content"></div>
            </div>
        </div>
        
        <script>
            let currentSessionId = null;
            
            function showTab(tabName) {
                // Hide all tabs
                document.querySelectorAll('.content').forEach(el => el.style.display = 'none');
                document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
                
                // Show selected tab
                document.getElementById(tabName + '-tab').style.display = 'block';
                event.target.classList.add('active');
            }
            
            async function submitQuery(event) {
                event.preventDefault();
                
                const question = document.getElementById('question').value;
                const loading = document.getElementById('query-loading');
                const response = document.getElementById('query-response');
                
                loading.style.display = 'block';
                response.innerHTML = '';
                
                try {
                    const result = await fetch('/query', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ 
                            question: question,
                            session_id: currentSessionId 
                        })
                    });
                    
                    const data = await result.json();
                    currentSessionId = data.session_id;
                    
                    let html = '<div class="response">';
                    html += `<h3>${data.success ? '✅ Success' : '❌ Error'}</h3>`;
                    html += `<p><strong>Answer:</strong> ${data.message}</p>`;
                    
                    if (data.sql_query) {
                        html += `<p><strong>SQL Query:</strong><br><code>${data.sql_query}</code></p>`;
                    }
                    
                    if (data.results && data.results.length > 0) {
                        html += `<p><strong>Results (${data.result_count}):</strong></p>`;
                        html += '<div style="max-height: 300px; overflow-y: auto;">';
                        html += '<table border="1" style="width: 100%; border-collapse: collapse;">';
                        
                        // Headers
                        const headers = Object.keys(data.results[0]);
                        html += '<tr>';
                        headers.forEach(header => html += `<th style="padding: 5px;">${header}</th>`);
                        html += '</tr>';
                        
                        // Data rows (first 10)
                        data.results.slice(0, 10).forEach(row => {
                            html += '<tr>';
                            headers.forEach(header => {
                                const value = row[header] || '';
                                html += `<td style="padding: 5px;">${String(value).substring(0, 100)}</td>`;
                            });
                            html += '</tr>';
                        });
                        
                        html += '</table></div>';
                        
                        if (data.results.length > 10) {
                            html += `<p><em>Showing first 10 of ${data.results.length} results</em></p>`;
                        }
                    }
                    
                    html += '</div>';
                    response.innerHTML = html;
                    
                } catch (error) {
                    response.innerHTML = `<div class="response error">
                        <h3>❌ Error</h3>
                        <p>Failed to process query: ${error.message}</p>
                    </div>`;
                } finally {
                    loading.style.display = 'none';
                }
            }
            
            async function sendChatMessage(event) {
                event.preventDefault();
                
                const message = document.getElementById('chat-message').value;
                const chatHistory = document.getElementById('chat-history');
                
                // Add user message
                chatHistory.innerHTML += `<div style="margin-bottom: 10px;">
                    <strong>You:</strong> ${message}
                </div>`;
                
                // Clear input
                document.getElementById('chat-message').value = '';
                
                try {
                    const result = await fetch('/chat', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ 
                            message: message,
                            session_id: currentSessionId 
                        })
                    });
                    
                    const data = await result.json();
                    currentSessionId = data.session_id;
                    
                    // Add assistant response
                    chatHistory.innerHTML += `<div style="margin-bottom: 10px; padding: 10px; 
                                                    background: #e8f4f8; border-radius: 4px;">
                        <strong>Assistant:</strong> ${data.message}
                    </div>`;
                    
                    // Scroll to bottom
                    chatHistory.scrollTop = chatHistory.scrollHeight;
                    
                } catch (error) {
                    chatHistory.innerHTML += `<div style="margin-bottom: 10px; color: red;">
                        <strong>Error:</strong> Failed to send message: ${error.message}
                    </div>`;
                }
            }
            
            async function loadSchema() {
                const loading = document.getElementById('schema-loading');
                const content = document.getElementById('schema-content');
                
                loading.style.display = 'block';
                content.innerHTML = '';
                
                try {
                    const result = await fetch('/schema/tables');
                    const data = await result.json();
                    
                    let html = '<h3>Database Tables</h3>';
                    html += '<div style="display: grid; gap: 15px;">';
                    
                    data.tables.forEach(table => {
                        html += `<div style="border: 1px solid #ddd; padding: 15px; border-radius: 4px;">
                            <h4>${table.name}</h4>
                            <p>Schema: ${table.schema} | Columns: ${table.columns}</p>
                        </div>`;
                    });
                    
                    html += '</div>';
                    content.innerHTML = html;
                    
                } catch (error) {
                    content.innerHTML = `<div class="error">
                        Failed to load schema: ${error.message}
                    </div>`;
                } finally {
                    loading.style.display = 'none';
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    # Recommended: run from project root with:
    # uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000
    uvicorn.run(
        "src.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )