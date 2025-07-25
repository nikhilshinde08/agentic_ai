# Healthcare Database Assistant

A comprehensive healthcare database assistant with natural language processing capabilities, featuring a React-based frontend and FastAPI backend. This application allows users to interact with healthcare databases using natural language queries and provides real-time analytics and monitoring.

## =� Features

- **Natural Language Database Queries**: Ask questions in plain English and get structured database responses
- **Interactive Chat Interface**: Modern, responsive chat widget with session management
- **Real-Time Analytics Dashboard**: Monitor API usage, response times, and storage metrics
- **Session Persistence**: Maintain conversation context across multiple interactions
- **Healthcare Data Focus**: Specialized tools for medical records, patient data, and healthcare information
- **Comprehensive API**: RESTful API with full documentation and monitoring capabilities

## <� Architecture

- **Frontend**: React + TypeScript + Vite + Tailwind CSS + shadcn/ui
- **Backend**: FastAPI + Python + SQLAlchemy + Azure OpenAI
- **Database**: PostgreSQL (configurable)
- **AI/ML**: Azure OpenAI GPT-4, LangChain, ReAct Agent pattern
- **Storage**: SQLite for API logs and analytics, file-based storage for detailed logs

## =� Prerequisites

Before running the application, ensure you have the following installed:

- **Python 3.8+** (recommended: 3.10+)
- **Node.js 16+** (recommended: 18+)
- **npm** or **yarn**
- **Git**

## =� Installation & Setup

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd healthcare-database-assistant
```

### 2. Environment Configuration

Create a `.env` file in the root directory with your configuration:

```env
# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=your_azure_openai_endpoint
AZURE_OPENAI_API_KEY=your_azure_openai_api_key
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT_NAME=your_deployment_name
AZURE_OPENAI_MODEL_NAME=gpt-4

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost/healthcare_db

# Optional: Tavily API for healthcare search
TAVILY_API_KEY=your_tavily_api_key_here
```

### 3. Backend Setup

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install
# or
yarn install

# Return to root directory
cd ..
```

## =� Running the Application

### Option 1: Quick Start (Recommended)

Use the automated startup script to run both frontend and backend:

```bash
# Make script executable
chmod +x start_full_stack.sh

# Start both servers
./start_full_stack.sh
```

This will:
- Kill any existing processes on ports 8002 and 3000
- Start the FastAPI backend on `http://127.0.0.1:8002`
- Start the React frontend on `http://localhost:3000`
- Automatically open API documentation at `http://127.0.0.1:8002/docs`

### Option 2: Manual Startup

#### Start Backend Only

```bash
# Make script executable
chmod +x start_backend.sh

# Start backend server
./start_backend.sh
```

Or manually:

```bash
# Activate virtual environment
source venv/bin/activate

# Start FastAPI server
python -m uvicorn api_server:app --host 127.0.0.1 --port 8002 --reload
```

#### Start Frontend Only

```bash
# Make script executable
chmod +x start_frontend.sh

# Start frontend server
./start_frontend.sh
```

Or manually:

```bash
cd frontend
npm run dev
# or
yarn dev
```

## < Access Points

Once running, you can access:

- **Frontend Application**: http://localhost:3000
- **Backend API**: http://127.0.0.1:8002
- **API Documentation**: http://127.0.0.1:8002/docs
- **Health Check**: http://127.0.0.1:8002/health
- **Analytics Endpoint**: http://127.0.0.1:8002/analytics

## <� How to Use

### 1. Chat Interface

- Click the chat icon in the bottom-right corner of the frontend
- Type natural language questions about healthcare data
- **New Feature**: Responses are now formatted as concise tables and summaries for easy reading
- Response format includes:
  - **SUMMARY**: One-sentence overview
  - **DATA**: Structured table (max 5 rows shown)
  - **KEY INSIGHTS**: 2-3 bullet points

Examples:
  - "How many patients do we have?"
  - "Show me patients with diabetes"
  - "What are the most common diagnoses?"
  - "Find patients admitted last month"

### 2. Analytics Dashboard

- Navigate to the "Analytics" tab in the sidebar
- Monitor real-time usage statistics
- View request patterns and response times
- Track storage usage and database metrics

### 3. API Integration

Use the REST API directly:

```bash
# Send a chat message
curl -X POST "http://127.0.0.1:8002/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "How many patients do we have?"}'

# Get analytics
curl "http://127.0.0.1:8002/analytics?days=7"

# Check health
curl "http://127.0.0.1:8002/health"
```

## =' Configuration Options

### Backend Configuration

- **Port**: Default 8002, configurable in startup scripts
- **Database**: Configure via `DATABASE_URL` environment variable
- **Azure OpenAI**: Configure via Azure-specific environment variables
- **Logging**: Logs stored in `logs/` directory
- **API Storage**: Analytics stored in `api_storage/` directory

### Frontend Configuration

- **Port**: Default 3000, automatically uses next available port
- **API Endpoint**: Configured to use `http://127.0.0.1:8002`
- **Theme**: Supports dark/light mode switching

## =� Monitoring & Analytics

The application provides comprehensive monitoring:

- **Request/Response Logging**: All API interactions are logged
- **Performance Metrics**: Response times, success rates, error tracking
- **Usage Analytics**: Daily/hourly usage patterns, session statistics
- **Storage Monitoring**: Database size, file storage usage
- **Real-time Dashboard**: Live updates of system metrics
- **JSON Storage**: Complete response data stored in JSON format for detailed analysis
- **Concise Chat Format**: Responses formatted as tables and summaries for better readability

## = Security Features

- **Input Validation**: All user inputs are validated and sanitized
- **Rate Limiting**: Configurable rate limits for API endpoints
- **Session Management**: Secure session handling with UUIDs
- **Error Handling**: Comprehensive error handling and logging
- **Environment Variables**: Sensitive data stored in environment variables

## =� Project Structure

```
healthcare-database-assistant/
   frontend/                 # React frontend application
      src/
         components/      # React components
         pages/           # Page components
         ...
      package.json
      ...
   src/                     # Python source code
      agents/              # AI agents and ReAct implementation
      storage/             # API storage and analytics
      memory/              # Memory management
      utils/               # Utility functions
   api_server.py            # FastAPI server implementation
   requirements.txt         # Python dependencies
   start_full_stack.sh      # Full stack startup script
   start_backend.sh         # Backend startup script
   start_frontend.sh        # Frontend startup script
   .env                     # Environment variables (create this)
   README.md               # This file
```

## =� Development

### Running Tests

```bash
# Backend tests
python -m pytest

# Frontend tests
cd frontend
npm test
```

### Building for Production

```bash
# Build frontend
cd frontend
npm run build

# The built files will be in frontend/dist/
```

## =� Troubleshooting

### Common Issues

1. **Port Already in Use**
   - The startup scripts will automatically kill existing processes on ports 8002 and 3000
   - No need to manually check for port conflicts - they're handled automatically

2. **Environment Variables Not Set**
   - Ensure `.env` file exists in root directory
   - Check that all required variables are set

3. **Database Connection Issues**
   - Verify database URL in `.env` file
   - Ensure database server is running
   - Check database credentials and permissions

4. **Azure OpenAI Configuration**
   - Verify Azure OpenAI endpoint and API key
   - Check deployment name and model configuration
   - Ensure API version is correct

### Getting Help

- Check the logs in `logs/` directory for detailed error information
- Visit the API documentation at `http://127.0.0.1:8002/docs`
- Use the health check endpoint to verify backend status

## > Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## =� License

This project is licensed under the MIT License - see the LICENSE file for details.

## =O Acknowledgments

- Built with FastAPI, React, and Azure OpenAI
- UI components from shadcn/ui
- Charts powered by Recharts
- Icons from Lucide React