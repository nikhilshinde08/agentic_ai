import asyncio
from agents.db_agent import DatabaseQueryAgent

async def main():
    agent = DatabaseQueryAgent()
    
    # Process a query
    result = await agent.process_query(
        "Show me all users older than 30",
        session_id="python_session"
    )
    
    if result["success"]:
        print(f"Generated SQL: {result['sql_query']}")
        print(f"Results: {result['data']}")
        print(f"Retry count: {result['retry_count']}")
    else:
        print(f"Error: {result['error_message']}")
        print(f"Error code: {result['error_code']}")

asyncio.run(main())