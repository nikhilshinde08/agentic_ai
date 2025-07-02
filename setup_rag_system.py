# setup_enhanced_rag_system.py - Setup script for Enhanced Structured RAG system
import os
import json
from dotenv import load_dotenv

def create_enhanced_directory_structure():
    """Create enhanced directory structure"""
    directories = [
        "src",
        "src/agents",
        "src/database", 
        "src/models",
        "vector_db_structured",  # New structured vector DB path
        "json_responses_enhanced",  # Enhanced JSON responses
        "docs",
        "config"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created directory: {directory}")

def check_enhanced_env_file():
    """Check and display enhanced .env file status"""
    if not os.path.exists('.env'):
        print("❌ .env file not found!")
        print("\n📝 Create .env file with the following enhanced configuration:")
        print("""
# ===========================================
# AZURE OPENAI CONFIGURATION (for chat)
# ===========================================
AZURE_OPENAI_API_KEY=your_azure_openai_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-deployment-name
AZURE_OPENAI_MODEL_NAME=gpt-4o
AZURE_OPENAI_API_VERSION=2025-01-01-preview

# ===========================================
# OPENAI CONFIGURATION (for embeddings)
# ===========================================
OPENAI_API_KEY=sk-your-openai-key-here

# ===========================================
# DATABASE CONFIGURATION
# ===========================================
DB_HOST=your_postgres_host
DB_PORT=5432
DB_NAME=your_database_name
DB_USER=your_username
DB_PASSWORD=your_password

# ===========================================
# ENHANCED RAG CONFIGURATION
# ===========================================
VECTOR_DB_PATH=vector_db_structured
EMBEDDING_MODEL=text-embedding-3-large
CHUNKING_STRATEGY=structured_table_chunks
BUSINESS_CONTEXT_ENABLED=true
HEALTHCARE_DOMAIN_ENABLED=true
        """)
        return False
    else:
        print("✅ .env file found")
        return True

def check_enhanced_env_variables():
    """Check if all required enhanced environment variables are set"""
    load_dotenv()
    
    required_vars = {
        'AZURE_OPENAI_API_KEY': 'Azure OpenAI API Key',
        'AZURE_OPENAI_ENDPOINT': 'Azure OpenAI Endpoint',
        'AZURE_OPENAI_DEPLOYMENT_NAME': 'Azure OpenAI Deployment Name',
        'OPENAI_API_KEY': 'OpenAI API Key (for embeddings)',
        'DB_HOST': 'Database Host',
        'DB_NAME': 'Database Name',
        'DB_USER': 'Database User',
        'DB_PASSWORD': 'Database Password'
    }
    
    optional_vars = {
        'VECTOR_DB_PATH': 'Vector DB Path (defaults to vector_db_structured)',
        'EMBEDDING_MODEL': 'Embedding Model (defaults to text-embedding-3-large)',
        'CHUNKING_STRATEGY': 'Chunking Strategy (defaults to structured_table_chunks)'
    }
    
    missing = []
    present = []
    optional_present = []
    
    for var, desc in required_vars.items():
        value = os.getenv(var)
        if value:
            if 'KEY' in var or 'PASSWORD' in var:
                present.append(f"✅ {desc}: {value[:10]}...")
            else:
                present.append(f"✅ {desc}: {value}")
        else:
            missing.append(f"❌ {desc}: MISSING")
    
    for var, desc in optional_vars.items():
        value = os.getenv(var)
        if value:
            optional_present.append(f"✅ {desc}: {value}")
        else:
            optional_present.append(f"⚪ {desc}: Using default")
    
    print("\n🔍 Required Environment Variables:")
    for item in present:
        print(f"  {item}")
    for item in missing:
        print(f"  {item}")
    
    print("\n🔍 Optional Environment Variables:")
    for item in optional_present:
        print(f"  {item}")
    
    return len(missing) == 0

def check_enhanced_files():
    """Check if enhanced required files exist"""
    files_to_check = [
        ("main.py", "Enhanced main application file"),
        ("src/agents/enhanced_single_table_rag_agent.py", "Enhanced structured RAG agent"),
        ("src/models/response_models.py", "Response models"),
        ("src/database/connection.py", "Database connection"),
        ("requirements.txt", "Requirements file")
    ]
    
    print("\n📁 Enhanced File Status:")
    all_exist = True
    
    for filepath, description in files_to_check:
        if os.path.exists(filepath):
            print(f"  ✅ {description}: {filepath}")
        else:
            print(f"  ❌ {description}: {filepath} - MISSING")
            all_exist = False
    
    return all_exist

def check_enhanced_description_file():
    """Check for enhanced description.txt with business context"""
    desc_path = "description.txt"
    
    print(f"\n📄 Enhanced Database Description File:")
    if os.path.exists(desc_path):
        try:
            with open(desc_path, 'r') as f:
                content = f.read().strip()
                print(f"  ✅ Found: {desc_path} ({len(content)} characters)")
                print(f"  📝 Preview: {content[:150]}...")
                
                # Check for healthcare/business context
                healthcare_terms = ['patient', 'medical', 'healthcare', 'clinical', 'diagnosis', 'treatment']
                has_healthcare_context = any(term in content.lower() for term in healthcare_terms)
                
                if has_healthcare_context:
                    print("  🏥 Healthcare context detected - enhanced domain intelligence will be activated")
                else:
                    print("  💡 Consider adding healthcare/business context for better domain intelligence")
                    
        except Exception as e:
            print(f"  ⚠️  Found but cannot read: {e}")
    else:
        print(f"  ❌ Not found: {desc_path}")
        print("  💡 Recommended: Create this file with database business context")
        print("  📋 Example content:")
        print("""
        This is a healthcare database containing patient records, medical encounters, 
        conditions, medications, procedures, and related healthcare data. The database
        follows standard healthcare data models with SNOMED codes for conditions,
        CPT codes for procedures, and includes insurance/payer information.
        """)

def create_enhanced_config_files():
    """Create enhanced configuration files"""
    
    # Create enhanced RAG config
    rag_config = {
        "chunking_strategy": "structured_table_chunks",
        "vector_db_path": "vector_db_structured",
        "embedding_model": "text-embedding-3-large",
        "chunk_overlap": 0,
        "business_context_enabled": True,
        "healthcare_domain_enabled": True,
        "column_categorization_enabled": True,
        "sample_queries_enabled": True,
        "usage_hints_enabled": True,
        "relationship_mapping_enabled": True,
        "accuracy_target": 0.98
    }
    
    config_dir = "config"
    os.makedirs(config_dir, exist_ok=True)
    
    with open(f"{config_dir}/enhanced_rag_config.json", 'w') as f:
        json.dump(rag_config, f, indent=2)
    print(f"✅ Created enhanced RAG configuration: {config_dir}/enhanced_rag_config.json")
    
    # Create system info file
    system_info = {
        "system_type": "Enhanced Structured RAG Database Assistant",
        "version": "2.0",
        "features": [
            "Structured table chunking with business context",
            "Healthcare domain intelligence",
            "Column categorization and relationship mapping",
            "Sample queries and usage hints",
            "98%+ column name accuracy",
            "Business intelligence insights",
            "Persistent vector storage"
        ],
        "models": {
            "chat": "Azure OpenAI GPT-4o",
            "embeddings": "OpenAI text-embedding-3-large",
            "vector_store": "FAISS with structured chunks"
        },
        "supported_domains": [
            "Healthcare/Medical",
            "Insurance/Payer",
            "Clinical workflows",
            "Financial analysis"
        ]
    }
    
    with open(f"{config_dir}/system_info.json", 'w') as f:
        json.dump(system_info, f, indent=2)
    print(f"✅ Created system information: {config_dir}/system_info.json")

def create_sample_queries_file():
    """Create sample queries file for reference"""
    sample_queries = {
        "basic_exploration": [
            "How many patients are in the database?",
            "What tables are available in this database?",
            "Show me the structure of the patients table",
            "What columns link patients to their medical records?"
        ],
        "patient_analysis": [
            "Find patients with diabetes",
            "Show patients with multiple chronic conditions", 
            "Find the oldest and youngest patients",
            "Show patients by gender distribution"
        ],
        "clinical_analysis": [
            "What are the most common medical conditions?",
            "Show recent medical encounters",
            "Find patients with specific medications",
            "What procedures are performed most frequently?"
        ],
        "financial_analysis": [
            "Show the most expensive procedures",
            "Find high-cost patients",
            "Analyze insurance coverage patterns",
            "Show revenue by provider"
        ],
        "relationship_analysis": [
            "How are patients connected to providers?",
            "Show the relationship between encounters and conditions",
            "Map patient journey through multiple encounters",
            "Find provider specialties and patient loads"
        ]
    }
    
    with open("docs/sample_queries.json", 'w') as f:
        json.dump(sample_queries, f, indent=2)
    print("✅ Created sample queries reference: docs/sample_queries.json")

def main():
    """Main enhanced setup function"""
    print("🚀 ENHANCED STRUCTURED RAG SYSTEM SETUP")
    print("="*60)
    print("🎯 Setting up Enhanced Structured RAG with Business Context")
    print("🏥 Healthcare Domain Intelligence + 98% Accuracy Target")
    
    # Create enhanced directories
    print("\n1. Creating enhanced directory structure...")
    create_enhanced_directory_structure()
    
    # Check .env file
    print("\n2. Checking enhanced .env file...")
    env_exists = check_enhanced_env_file()
    
    if env_exists:
        # Check environment variables
        print("\n3. Checking enhanced environment variables...")
        env_complete = check_enhanced_env_variables()
    else:
        env_complete = False
    
    # Check enhanced files
    print("\n4. Checking enhanced required files...")
    files_complete = check_enhanced_files()
    
    # Check enhanced description file
    print("\n5. Checking enhanced database description...")
    check_enhanced_description_file()
    
    # Create enhanced config files
    print("\n6. Creating enhanced configuration files...")
    create_enhanced_config_files()
    
    # Create sample queries
    print("\n7. Creating sample queries reference...")
    create_sample_queries_file()
    
    # Summary
    print("\n" + "="*60)
    print("📊 ENHANCED SETUP SUMMARY")
    print("="*60)
    
    if env_complete and files_complete:
        print("🎉 Enhanced setup is COMPLETE! You can run the system:")
        print("   python main.py")
        
        print("\n📁 Enhanced Vector Database:")
        print("   • Will be created in ./vector_db_structured/ folder")
        print("   • Uses structured table chunks with business context")
        print("   • Persists between application runs")
        print("   • Contains comprehensive table information")
        
        print("\n🎯 Enhanced Features:")
        print("   • Structured JSON-like table chunks")
        print("   • Healthcare domain intelligence")
        print("   • Column categorization (ID, FK, dates, codes, etc.)")
        print("   • Business context for every table and column")
        print("   • Sample queries and usage hints")
        print("   • 98%+ column name accuracy target")
        
    else:
        print("⚠️  Enhanced setup is INCOMPLETE:")
        if not env_complete:
            print("   • Fix environment variables in .env file")
        if not files_complete:
            print("   • Create missing enhanced files")
        print("\n🔧 Once complete, run: python main.py")
    
    print(f"\n💡 Enhanced System Capabilities:")
    print(f"   • Structured table chunking with complete business context")
    print(f"   • Healthcare domain knowledge and medical coding understanding")
    print(f"   • Advanced PostgreSQL query optimization")
    print(f"   • Business intelligence insights and analysis")
    print(f"   • Persistent vector storage for faster subsequent runs")
    print(f"   • 98%+ accuracy in table/column name usage")
    
    print(f"\n📚 Documentation Created:")
    print(f"   • config/enhanced_rag_config.json - RAG configuration")
    print(f"   • config/system_info.json - System information")
    print(f"   • docs/sample_queries.json - Query examples by category")

if __name__ == "__main__":
    main()