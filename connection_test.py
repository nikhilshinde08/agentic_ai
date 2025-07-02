# connection_test.py - Simple test for the database connection fix
import asyncio
import os
import sys
from dotenv import load_dotenv

# Add src to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

async def test_database_connection():
    """Test database connection with the fixed approach"""
    print("🧪 Testing Database Connection with Fixed Approach")
    print("=" * 50)
    
    try:
        from database.connection import DatabaseConnection
        
        # Test basic connection
        db = DatabaseConnection()
        connected, error = await db.test_connection()
        
        if not connected:
            print(f"❌ Database connection failed: {error}")
            return False
        
        print("✅ Database connection successful")
        
        # Test simple query
        print("\n🔍 Testing simple query...")
        success, data, error, status_code = await db.execute_query("SELECT 1 as test;")
        
        if success:
            print("✅ Simple query successful")
        else:
            print(f"❌ Simple query failed: {error}")
            return False
        
        # Test schema query
        print("\n🔍 Testing schema query...")
        schema_query = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' LIMIT 3;"
        success, data, error, status_code = await db.execute_query(schema_query)
        
        if success:
            print(f"✅ Schema query successful - found {len(data)} tables")
            if data:
                table_names = [row['table_name'] for row in data]
                print(f"📋 Available tables: {table_names}")
                
                # Test column query on first table
                if table_names:
                    first_table = table_names[0]
                    print(f"\n🔍 Testing column query on '{first_table}'...")
                    col_query = f"SELECT column_name FROM information_schema.columns WHERE table_name = '{first_table}' LIMIT 5;"
                    success, data, error, status_code = await db.execute_query(col_query)
                    
                    if success:
                        print(f"✅ Column query successful - found {len(data)} columns")
                        if data:
                            column_names = [row['column_name'] for row in data]
                            print(f"📋 Available columns: {column_names}")
                        return True
                    else:
                        print(f"❌ Column query failed: {error}")
                        return False
        else:
            print(f"❌ Schema query failed: {error}")
            return False
            
    except Exception as e:
        print(f"❌ Test exception: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_tool_execution():
    """Test the fixed DatabaseQueryTool"""
    print("\n🧪 Testing Fixed DatabaseQueryTool")
    print("=" * 50)
    
    try:
        from agents.rag_react_agent import DatabaseQueryTool
        from database.connection import DatabaseConnection
        
        # Create tool instance
        db = DatabaseConnection()
        tool = DatabaseQueryTool(db_connection=db)
        
        # Test simple query
        print("🔍 Testing tool with simple query...")
        result = tool._run("SELECT 1 as test;")
        
        if "✅" in result:
            print("✅ Tool execution successful")
            print(f"📊 Result preview: {result[:200]}...")
            
            # Test schema query
            print("\n🔍 Testing tool with schema query...")
            schema_result = tool._run("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' LIMIT 3;")
            
            if "✅" in schema_result:
                print("✅ Schema query through tool successful")
                return True
            else:
                print(f"❌ Schema query through tool failed: {schema_result[:200]}...")
                return False
        else:
            print(f"❌ Tool execution failed: {result[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ Tool test exception: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    load_dotenv()
    
    print("🔧 DATABASE CONNECTION AND QUERY EXECUTION FIX TEST")
    print("=" * 60)
    
    # Test 1: Direct database connection
    db_success = await test_database_connection()
    
    # Test 2: Tool execution
    tool_success = test_tool_execution()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    print(f"Direct Database Connection: {'✅ PASS' if db_success else '❌ FAIL'}")
    print(f"Tool Execution: {'✅ PASS' if tool_success else '❌ FAIL'}")
    
    if db_success and tool_success:
        print("\n🎉 All tests passed! The connection and execution fixes are working.")
        print("   You can now try running the enhanced RAG system again.")
        print("   The async event loop conflicts should be resolved.")
    else:
        print("\n⚠️  Some tests failed. Check the error messages above.")
        print("💡 Common solutions:")
        print("   • Ensure your .env file has correct database credentials")
        print("   • Check that the database is accessible")
        print("   • Verify the database contains the expected tables")

if __name__ == "__main__":
    asyncio.run(main())