# src/models/response_models.py - Complete Response Models
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

class QueryResult(BaseModel):
    """Individual query result record"""
    data: Dict[str, Any] = Field(..., description="Record data")
    
    @validator('data', pre=True)
    def validate_data(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return {"raw_data": v}
        return v if isinstance(v, dict) else {"value": v}

class DatabaseResponse(BaseModel):
    """Main database response model"""
    success: bool = Field(..., description="Query success status")
    message: str = Field(..., description="Response message")
    query_understanding: str = Field(..., description="How the AI interpreted the question")
    sql_query: Optional[str] = Field(None, description="Generated SQL query")
    result_count: int = Field(0, description="Number of results")
    results: List[QueryResult] = Field(default_factory=list, description="Query results")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    powered_by: str = Field(default="Column-Level RAG Agent", description="AI system used")
    
    @validator('results', pre=True)
    def validate_results(cls, v):
        if not v:
            return []
        
        validated_results = []
        for item in v:
            if isinstance(item, dict):
                validated_results.append(QueryResult(data=item))
            else:
                validated_results.append(QueryResult(data={"value": str(item)}))
        return validated_results
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }