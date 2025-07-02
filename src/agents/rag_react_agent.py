# agents/rag_react_agent.py
import os
import json
import re
from typing import Dict, Any, List, Optional, Annotated, Literal
from langchain_openai import AzureChatOpenAI, OpenAIEmbeddings
from langchain_core.tools import tool
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
import structlog
from dotenv import load_dotenv

load_dotenv()
logger = structlog.get_logger(__name__)

class EnhancedStructuredRAGRetriever:
    def __init__(self, db_connection):
        self.db_connection = db_connection
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-large",
            api_key=os.getenv('OPENAI_API_KEY')
        )
        self.vectorstore = None
        self.vector_db_path = "vector_db_structured"
        self.schema_description = self._load_description_file()
        os.makedirs(self.vector_db_path, exist_ok=True)

    def _load_description_file(self) -> Dict[str, Any]:
        try:
            # Try loading from description.json first, then description.txt
            for filename in ["description.json", "description.txt"]:
                if os.path.exists(filename):
                    with open(filename, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                        schema_data = json.loads(content)
                        logger.info(f"✅ Loaded database schema from {filename}")
                        return schema_data
            logger.warning("No description file found (description.json or description.txt)")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in description file: {e}")
            return {}
        except Exception as e:
            logger.warning(f"Could not load description file: {e}")
            return {}

    async def initialize_rag(self):
        vector_db_file = os.path.join(self.vector_db_path, "structured_table_vectordb")
        if os.path.exists(vector_db_file):
            try:
                logger.info(f"🔄 Loading existing vector database from {vector_db_file}")
                self.vectorstore = FAISS.load_local(
                    vector_db_file, self.embeddings, allow_dangerous_deserialization=True
                )
                return
            except Exception as e:
                logger.warning(f"Failed to load existing vector DB: {e}. Creating new one...")
        
        # Create key-based chunks from the schema
        documents = []
        if self.schema_description:
            chunks = create_key_based_chunks(self.schema_description)
            for chunk in chunks:
                documents.append(Document(
                    page_content=chunk["text"],
                    metadata={
                        "chunk_type": chunk["type"],
                        "table_name": chunk.get("table_name"),
                        "key": chunk.get("key")
                    }
                ))
        
        if documents:
            self.vectorstore = FAISS.from_documents(documents, self.embeddings)
            self.vectorstore.save_local(vector_db_file)
            logger.info(f"✅ Key-based vector database created and saved to {vector_db_file} with {len(documents)} chunks")
        else:
            logger.error("No documents created from schema. Check your description file.")

    def retrieve_relevant_schema(self, query: str, k: int = 5) -> str:
        logger.info(f"[RAG TOOL] Called with query: {query}")
        if not self.vectorstore:
            return "RAG system not initialized"
        
        try:
            docs = self.vectorstore.similarity_search(query, k=k)
            relevant_tables = set()
            relevant_info = []
            
            for doc in docs:
                metadata = doc.metadata
                chunk_type = metadata.get("chunk_type", "unknown")
                table_name = metadata.get("table_name")
                
                if chunk_type == "table_overview" and table_name:
                    relevant_tables.add(table_name)
                    relevant_info.append(f"Table: {table_name}")
                elif chunk_type == "table_columns" and table_name:
                    relevant_tables.add(table_name)
                    # Extract column names from the content
                    content = doc.page_content
                    column_matches = re.findall(r'Column: ([A-Z_]+)', content)
                    if column_matches:
                        relevant_info.append(f"Columns in {table_name}: {', '.join(column_matches[:5])}")
                elif chunk_type == "relationships":
                    relevant_info.append("Relationship information found")
            
            # Fallback: extract table names from content if metadata doesn't help
            if not relevant_tables:
                for doc in docs:
                    content = doc.page_content
                    table_matches = re.findall(r'(?:Table|table):\s*([A-Z_]{3,})', content)
                    relevant_tables.update(table_matches)
            
            if relevant_tables:
                tables_list = list(relevant_tables)
                result = f"Relevant tables: {', '.join(tables_list)}.\n"
                if relevant_info:
                    result += f"Additional info: {'; '.join(relevant_info[:3])}.\n"
                result += (
                    "Now proceed to call the 'sql_db_query' tool with a valid SQL SELECT statement using these tables.\n"
                    "Do NOT call 'rag_schema_query' again for this question."
                )
                return result
            else:
                return (
                    "Schema lookup completed. Now call the 'sql_db_query' tool with your best guess for table names."
                )
                
        except Exception as e:
            logger.error(f"RAG retrieval failed: {e}")
            return f"Error retrieving schema: {str(e)}"

    def get_vector_db_info(self) -> Dict[str, Any]:
        vector_db_file = os.path.join(self.vector_db_path, "structured_table_vectordb")
        return {
            "vector_db_path": self.vector_db_path,
            "vector_db_file": vector_db_file,
            "exists": os.path.exists(vector_db_file)
        }

# Global instances for tools (initialized later)
rag_retriever_instance = None
db_connection_instance = None

@tool
def rag_schema_query(query: str) -> str:
    """Look up which tables and columns to use. Use only once per user question. 
    Returns a minimal, concise list of table and column names relevant to the question."""
    logger.info(f"[TOOL] rag_schema_query called with: {query}")
    return rag_retriever_instance.retrieve_relevant_schema(query, k=3)

@tool
def sql_db_query(query: str) -> str:
    """Run a SELECT SQL query on the healthcare PostgreSQL database. 
    Use UPPERCASE table/column names (ID, PATIENT, etc)."""
    logger.info(f"[TOOL] sql_db_query called with: {query}")
    
    try:
        import asyncio
        query = query.strip()
        if not query.endswith(';'):
            query += ';'

        def execute_in_new_thread():
            try:
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                from database.connection import DatabaseConnection
                fresh_db = DatabaseConnection()
                try:
                    result = new_loop.run_until_complete(fresh_db.execute_query(query))
                    return result
                finally:
                    try:
                        new_loop.run_until_complete(fresh_db.close())
                    except:
                        pass
                    new_loop.close()
            except Exception as e:
                return False, [], f"Thread execution error: {str(e)}", 500

        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(execute_in_new_thread)
            try:
                success, data, error, status_code = future.result(timeout=45)
            except concurrent.futures.TimeoutError:
                return "❌ Query execution timed out. Try a simpler query."

        if success:
            if data:
                headers = list(data[0].keys()) if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict) else []
                preview = json.dumps(data[:3], default=str, indent=2) if isinstance(data, list) else str(data)[:400]
                return (
                    f"✅ Query executed successfully! Found {len(data)} records.\n"
                    f"Sample: {preview}\n"
                    "After this, DO NOT call any more tools. Respond to the user."
                )
            else:
                return "✅ Query ran but returned no results."
        else:
            return f"❌ Query failed: {error}"
            
    except Exception as e:
        logger.error(f"DatabaseQueryTool execution error: {e}")
        return f"❌ Tool error: {str(e)}"

class EnhancedStructuredRAGAgent:
    def __init__(self):
        self.llm = AzureChatOpenAI(
            azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'),
            api_key=os.getenv('AZURE_OPENAI_API_KEY'),
            api_version=os.getenv('AZURE_OPENAI_API_VERSION'),
            deployment_name=os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME'),
            model=os.getenv('AZURE_OPENAI_MODEL_NAME', 'gpt-4o'),
            temperature=0.1
        )
        
        from database.connection import DatabaseConnection
        self.db_connection = DatabaseConnection()
        self.rag_retriever = EnhancedStructuredRAGRetriever(self.db_connection)
        
        # Initialize global instances for tools
        global rag_retriever_instance, db_connection_instance
        rag_retriever_instance = self.rag_retriever
        db_connection_instance = self.db_connection
        
        self.tools = [rag_schema_query, sql_db_query]
        self.system_prompt = self._create_enhanced_system_prompt()
        self.memory = MemorySaver()
        self.graph = self._create_graph()

    def _create_enhanced_system_prompt(self) -> str:
        return """
You are an expert healthcare SQL assistant.
You have two tools:
- rag_schema_query: Use this ONCE per user question, ONLY if you need to look up table/column names.
- sql_db_query: Use this to run SQL SELECT queries and fetch data.

**Rules:**
- Call rag_schema_query at most once per question. Do NOT call it more than once!
- After rag_schema_query, immediately proceed to sql_db_query to answer the question.
- Use UPPERCASE for all table and column names.
- After running sql_db_query and seeing the result, respond directly to the user and do NOT call any more tools.

**Examples:**
User: What columns are in the PATIENTS table?
Action: rag_schema_query ("PATIENTS columns")
Observation: (see table/columns)
Final Answer: (tell user the columns)

User: List 3 male patients
Action: rag_schema_query ("PATIENTS, gender")
Action: sql_db_query ("SELECT ID, FIRST, LAST, GENDER FROM PATIENTS WHERE GENDER = 'M' LIMIT 3;")
Observation: (see data)
Final Answer: (show results and stop)

If you already called rag_schema_query, never call it again for this question!
"""

    def _create_graph(self) -> StateGraph:
        # Create the graph
        workflow = StateGraph(MessagesState)
        
        # Add nodes
        workflow.add_node("agent", self._call_model)
        workflow.add_node("tools", ToolNode(self.tools))
        
        # Add edges
        workflow.add_edge(START, "agent")
        workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            {"continue": "tools", "end": END}
        )
        workflow.add_edge("tools", "agent")
        
        return workflow.compile(checkpointer=self.memory)

    def _call_model(self, state: MessagesState):
        messages = state["messages"]
        
        # Add system message to the conversation
        system_msg = HumanMessage(content=self.system_prompt)
        
        # Bind tools to the model
        llm_with_tools = self.llm.bind_tools(self.tools)
        
        # Invoke with all messages including system prompt
        all_messages = [system_msg] + messages
        response = llm_with_tools.invoke(all_messages)
        
        return {"messages": [response]}

    def _should_continue(self, state: MessagesState) -> Literal["continue", "end"]:
        messages = state["messages"]
        last_message = messages[-1]
        
        # If the last message has tool calls, continue to tools
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "continue"
        return "end"

    async def initialize(self):
        logger.info("🔧 Initializing Enhanced Structured RAG Agent...")
        connected, error = await self.db_connection.test_connection()
        if not connected:
            raise Exception(f"Database connection failed: {error}")
        await self.rag_retriever.initialize_rag()
        logger.info("✅ Enhanced Structured RAG Agent ready!")

    def get_vector_db_info(self) -> Dict[str, Any]:
        return self.rag_retriever.get_vector_db_info()

    async def process_query(self, user_question: str):
        logger.info(f"🧠 Processing query: {user_question}")
        
        config = {"configurable": {"thread_id": "1"}}
        
        # Create initial state with user message
        initial_state = {
            "messages": [HumanMessage(content=user_question)]
        }
        
        # Run the graph
        result = await self.graph.ainvoke(initial_state, config)
        
        return self._parse_enhanced_agent_response(result, user_question)

    def _parse_enhanced_agent_response(self, agent_result: Dict, user_question: str) -> Dict[str, Any]:
        try:
            messages = agent_result.get("messages", [])
            if not messages:
                raise ValueError("No messages in agent result")
            
            # Find the final AI message
            final_message = None
            sql_query = None
            
            # Look through all messages to find SQL queries and the final response
            for msg in messages:
                # Check if it's an AI message with content
                if isinstance(msg, AIMessage) and hasattr(msg, 'content') and msg.content:
                    # Extract SQL query if present
                    if not sql_query:
                        sql_patterns = [
                            r'```sql\s*(SELECT.*?)```',
                            r'```\s*(SELECT.*?)```',
                            r'(SELECT[^;]*;)',
                            r'sql_db_query.*?"(SELECT[^"]*)"'
                        ]
                        
                        for pattern in sql_patterns:
                            sql_match = re.search(pattern, msg.content, re.IGNORECASE | re.DOTALL)
                            if sql_match:
                                sql_query = sql_match.group(1).strip()
                                break
                    
                    # Keep the last AI message as the final message
                    final_message = msg.content
            
            if not final_message:
                raise ValueError("No final message found")
            
            # Determine success based on message content
            success_indicators = [
                "✅", "successful", "found", "results", "records", "data", 
                "query executed", "retrieved", "analysis", "insights"
            ]
            error_indicators = [
                "❌", "error", "failed", "exception", "invalid", "syntax", 
                "not found", "cannot", "unable", "does not exist"
            ]
            
            message_lower = final_message.lower()
            success_score = sum(1 for indicator in success_indicators if indicator in message_lower)
            error_score = sum(1 for indicator in error_indicators if indicator in message_lower)
            
            has_sql_result = "query executed successfully" in message_lower
            has_data_insights = any(term in message_lower for term in ["records", "data", "results", "found"])
            has_error = "column" in message_lower and "does not exist" in message_lower
            
            is_successful = (success_score > error_score) or has_sql_result or has_data_insights
            if has_error:
                is_successful = False
            
            # Extract result count
            count_patterns = [
                r'found (\d+) records',
                r'(\d+) records returned',
                r'returned (\d+) results',
                r'found (\d+) results',
                r'(\d+) rows'
            ]
            
            result_count = 0
            for pattern in count_patterns:
                count_match = re.search(pattern, final_message, re.IGNORECASE)
                if count_match:
                    result_count = int(count_match.group(1))
                    break
            
            insights = self._extract_business_insights(final_message)
            
            return {
                "success": is_successful,
                "message": final_message[:800] + "..." if len(final_message) > 800 else final_message,
                "query_understanding": f"Enhanced analysis of: {user_question}",
                "sql_query": sql_query,
                "result_count": result_count,
                "results": [],
                "business_insights": insights,
                "metadata": {
                    "agent_type": "enhanced_structured_rag",
                    "vector_db_used": True,
                    "structured_chunks": True,
                    "success_score": success_score,
                    "error_score": error_score,
                    "has_business_context": len(insights) > 0,
                    "uppercase_columns_enforced": True
                }
            }
            
        except Exception as e:
            logger.error(f"Error parsing enhanced response: {e}")
            return {
                "success": False,
                "message": "Enhanced response parsing failed",
                "query_understanding": user_question,
                "sql_query": None,
                "result_count": 0,
                "results": [],
                "metadata": {
                    "parse_error": str(e),
                    "agent_type": "enhanced_structured_rag"
                }
            }

    def _extract_business_insights(self, message: str) -> List[str]:
        insights = []
        insight_patterns = [
            r'insights?:([^\.]+)',
            r'analysis:([^\.]+)',
            r'finding:([^\.]+)',
            r'observation:([^\.]+)',
            r'💡([^\.]+)',
            r'📊([^\.]+)',
            r'📈([^\.]+)'
        ]
        
        for pattern in insight_patterns:
            matches = re.findall(pattern, message, re.IGNORECASE)
            for match in matches:
                insight = match.strip()
                if len(insight) > 10:
                    insights.append(insight)
        
        return insights[:5]

# Factory function
async def create_enhanced_structured_rag_agent():
    agent = EnhancedStructuredRAGAgent()
    await agent.initialize()
    return agent

# --------------------- Key-based chunking utility ---------------------

def create_key_based_chunks(schema_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Creates key-based chunks from the JSON schema for better retrieval.
    
    Args:
        schema_data: The parsed JSON schema dictionary
    
    Returns:
        List of chunk dictionaries with type, table_name, key, and text
    """
    chunks = []
    
    if not schema_data or "tables" not in schema_data:
        logger.warning("Invalid schema data structure")
        return chunks
    
    # 1. Create table overview chunks
    for table in schema_data["tables"]:
        table_name = table["name"]
        description = table.get("description", "")
        
        # Table overview chunk
        overview_text = f"Table: {table_name}\nDescription: {description}"
        if "identification_fields" in table:
            overview_text += f"\nKey Fields: {', '.join(table['identification_fields'])}"
        if "date_fields" in table:
            overview_text += f"\nDate Fields: {', '.join(table['date_fields'])}"
        
        chunks.append({
            "type": "table_overview",
            "table_name": table_name,
            "key": f"table_{table_name.lower()}",
            "text": overview_text
        })
        
        # 2. Create column chunks (grouped by table)
        if "columns" in table:
            columns_text = f"Table: {table_name} - Columns:\n"
            for col in table["columns"]:
                col_name = col["name"]
                col_type = col.get("type", "unknown")
                col_desc = col.get("description", "")
                columns_text += f"Column: {col_name} ({col_type}) - {col_desc}\n"
            
            chunks.append({
                "type": "table_columns",
                "table_name": table_name,
                "key": f"columns_{table_name.lower()}",
                "text": columns_text
            })
            
            # 3. Create individual column chunks for important tables
            if table_name in ["PATIENTS", "ENCOUNTERS", "MEDICATIONS", "CONDITIONS"]:
                for col in table["columns"]:
                    col_name = col["name"]
                    col_type = col.get("type", "unknown")
                    col_desc = col.get("description", "")
                    
                    col_text = f"Table: {table_name}\nColumn: {col_name}\nType: {col_type}\nDescription: {col_desc}"
                    
                    chunks.append({
                        "type": "column_detail",
                        "table_name": table_name,
                        "key": f"col_{table_name.lower()}_{col_name.lower()}",
                        "text": col_text
                    })
    
    # 4. Create relationship chunks
    if "relationships" in schema_data:
        relationships_text = "Database Relationships:\n"
        for rel in schema_data["relationships"]:
            from_table = rel["from_table"]
            from_col = rel["from_column"]
            to_table = rel["to_table"]
            to_col = rel["to_column"]
            rel_type = rel.get("relationship", "unknown")
            
            relationships_text += f"{from_table}.{from_col} -> {to_table}.{to_col} ({rel_type})\n"
        
        chunks.append({
            "type": "relationships",
            "table_name": None,
            "key": "relationships_all",
            "text": relationships_text
        })
        
        # 5. Create table-specific relationship chunks
        table_relationships = {}
        for rel in schema_data["relationships"]:
            from_table = rel["from_table"]
            to_table = rel["to_table"]
            
            if from_table not in table_relationships:
                table_relationships[from_table] = []
            if to_table not in table_relationships:
                table_relationships[to_table] = []
                
            table_relationships[from_table].append(rel)
            table_relationships[to_table].append(rel)
        
        for table_name, rels in table_relationships.items():
            rel_text = f"Table: {table_name} - Related Tables:\n"
            related_tables = set()
            
            for rel in rels:
                if rel["from_table"] == table_name:
                    related_tables.add(rel["to_table"])
                    rel_text += f"References: {rel['to_table']}.{rel['to_column']} via {rel['from_column']}\n"
                else:
                    related_tables.add(rel["from_table"])
                    rel_text += f"Referenced by: {rel['from_table']}.{rel['from_column']} via {rel['to_column']}\n"
            
            rel_text += f"All related tables: {', '.join(sorted(related_tables))}"
            
            chunks.append({
                "type": "table_relationships",
                "table_name": table_name,
                "key": f"relations_{table_name.lower()}",
                "text": rel_text
            })
    
    logger.info(f"Created {len(chunks)} key-based chunks")
    return chunks