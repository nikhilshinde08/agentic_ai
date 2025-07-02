# query_debugger.py - Debug database query execution issues
import asyncio
import os
import sys
from dotenv import load_dotenv

# Add src to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

class QueryDebugger:
    """Debug database query execution"""
    
    def __init__(self):
        self.db_connection = None
    
    async def initialize(self):
        """Initialize database connection"""
        try:
            from database.connection import DatabaseConnection
            self.db_connection = DatabaseConnection()
            
            # Test connection
            connected, error = await self.db_connection.test_connection()
            if connected:
                print("✅ Database connection successful")
                return True
            else:
                print(f"❌ Database connection failed: {error}")
                return False
        except Exception as e:
            print(f"❌ Failed to initialize database: {e}")
            return False
    
    async def test_simple_query(self):
        """Test a simple query"""
        print("\n🧪 Testing simple query...")
        
        simple_queries = [
            "SELECT 1 as test;",
            "SELECT version();",
            "SELECT current_database();",
            "SELECT current_user;"
        ]
        
        for query in simple_queries:
            try:
                print(f"  Testing: {query}")
                success, data, error, status_code = await self.db_connection.execute_query(query)
                
                if success:
                    print(f"    ✅ Success: {data}")
                else:
                    print(f"    ❌ Failed: {error}")
            except Exception as e:
                print(f"    ❌ Exception: {e}")
    
    async def test_schema_queries(self):
        """Test schema-related queries"""
        print("\n🧪 Testing schema queries...")
        
        schema_queries = [
            "SELECT schemaname, tablename FROM pg_tables WHERE schemaname = 'public' LIMIT 5;",
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' LIMIT 5;",
            "SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = 'public' LIMIT 10;"
        ]
        
        for query in schema_queries:
            try:
                print(f"  Testing: {query[:50]}...")
                success, data, error, status_code = await self.db_connection.execute_query(query)
                
                if success:
                    print(f"    ✅ Success: Found {len(data) if data else 0} results")
                    if data:
                        print(f"    📊 Sample: {data[0] if data else 'No data'}")
                else:
                    print(f"    ❌ Failed: {error}")
            except Exception as e:
                print(f"    ❌ Exception: {e}")
    
    async def test_table_queries(self):
        """Test actual table queries"""
        print("\n🧪 Testing table queries...")
        
        # First, get available tables
        try:
            success, tables_data, error, _ = await self.db_connection.execute_query(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' LIMIT 5;"
            )
            
            if not success or not tables_data:
                print("    ❌ Cannot get table list")
                return
            
            table_names = [row['table_name'] for row in tables_data]
            print(f"    📋 Available tables: {table_names}")
            
            # Test queries on first table
            if table_names:
                first_table = table_names[0]
                test_queries = [
                    f"SELECT COUNT(*) FROM {first_table};",
                    f"SELECT * FROM {first_table} LIMIT 1;",
                    f"SELECT column_name FROM information_schema.columns WHERE table_name = '{first_table}' LIMIT 5;"
                ]
                
                for query in test_queries:
                    try:
                        print(f"  Testing: {query}")
                        success, data, error, status_code = await self.db_connection.execute_query(query)
                        
                        if success:
                            print(f"    ✅ Success: {len(data) if data else 0} results")
                            if data:
                                print(f"    📊 Sample: {data[0] if data else 'No data'}")
                        else:
                            print(f"    ❌ Failed: {error}")
                    except Exception as e:
                        print(f"    ❌ Exception: {e}")
                        
        except Exception as e:
            print(f"    ❌ Table query exception: {e}")
    
    async def test_tool_execution(self):
        """Test the actual DatabaseQueryTool execution"""
        print("\n🧪 Testing DatabaseQueryTool execution...")
        
        try:
            from agents.enhanced_single_table_rag_agent import DatabaseQueryTool
            
            # Create tool instance
            tool = DatabaseQueryTool(db_connection=self.db_connection)
            
            # Test simple queries
            test_queries = [
                "SELECT 1 as test;",
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';"
            ]
            
            for query in test_queries:
                try:
                    print(f"  Testing tool with: {query}")
                    result = tool._run(query)
                    print(f"    ✅ Tool result: {result[:200]}...")
                except Exception as e:
                    print(f"    ❌ Tool exception: {e}")
                    import traceback
                    traceback.print_exc()
        
        except Exception as e:
            print(f"    ❌ Tool import/creation failed: {e}")
    
    async def run_full_debug(self):
        """Run complete debugging sequence"""
        print("🔍 DATABASE QUERY EXECUTION DEBUGGER")
        print("=" * 50)
        
        # Initialize
        if not await self.initialize():
            return
        
        # Run tests
        await self.test_simple_query()
        await self.test_schema_queries()
        await self.test_table_queries()
        await self.test_tool_execution()
        
        print("\n" + "=" * 50)
        print("🎯 DEBUG COMPLETE")
        print("If all tests passed, query execution should work correctly.")
        print("If any tests failed, check the specific error messages above.")

async def debug_specific_query(query: str):
    """Debug a specific query"""
    print(f"🔍 DEBUGGING SPECIFIC QUERY: {query}")
    print("=" * 50)
    
    debugger = QueryDebugger()
    if not await debugger.initialize():
        return
    
    try:
        print("Testing direct database execution...")
        success, data, error, status_code = await debugger.db_connection.execute_query(query)
        
        if success:
            print(f"✅ Direct execution successful: {len(data) if data else 0} results")
            if data:
                print(f"📊 Sample data: {data[0] if data else 'No data'}")
        else:
            print(f"❌ Direct execution failed: {error}")
        
        print("\nTesting through DatabaseQueryTool...")
        from agents.enhanced_single_table_rag_agent import DatabaseQueryTool
        tool = DatabaseQueryTool(db_connection=debugger.db_connection)
        result = tool._run(query)
        print(f"🔧 Tool result: {result}")
        
    except Exception as e:
        print(f"❌ Debug exception: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Main debug function"""
    load_dotenv()
    
    if len(sys.argv) > 1:
        # Debug specific query
        query = " ".join(sys.argv[1:])
        await debug_specific_query(query)
    else:
        # Run full debug
        debugger = QueryDebugger()
        await debugger.run_full_debug()

if __name__ == "__main__":
    print("Usage:")
    print("  python query_debugger.py                    # Run full debug")
    print("  python query_debugger.py 'SELECT COUNT(*) FROM patients;'  # Debug specific query")
    print()
    
    asyncio.run(main())