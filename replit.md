# Multi-Agent GenAI System

## Overview

This is a sophisticated multi-agent pharmaceutical data analysis system built with Python, LangGraph, and FastMCP architecture. The system processes complex queries about pharmaceutical data by breaking them down into sub-questions and routing them to specialized agents. It features a Streamlit frontend and uses Google Gemini as the primary LLM for orchestration and analysis.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

The application follows a multi-agent orchestration pattern with the following key architectural decisions:

### **Agent-Based Architecture**
- **Problem**: Complex pharmaceutical queries require different types of data access and analysis
- **Solution**: Specialized agents for different data sources (CAPA files, Neo4j graph database, vector search, email)
- **Rationale**: Separation of concerns allows for better maintainability and scalability
- **Pros**: Modular design, easy to extend, specialized expertise per agent
- **Cons**: Increased complexity in coordination

### **LangGraph Workflow Orchestration**
- **Problem**: Need to coordinate multiple agents and manage state across complex workflows
- **Solution**: StateGraph from LangGraph with typed state management
- **Rationale**: Provides structured workflow management with state persistence
- **Pros**: Clear workflow visualization, state management, error handling
- **Cons**: Learning curve for LangGraph concepts

### **FastMCP Module Pattern**
- **Problem**: Need standardized way to interact with different data sources
- **Solution**: MCP (Model Context Protocol) modules for each data source
- **Rationale**: Consistent interface pattern across different backends
- **Pros**: Standardized interfaces, easy mocking for development, pluggable architecture
- **Cons**: Additional abstraction layer

## Key Components

### **1. Orchestrator Agent (`agents/orchestrator.py`)**
- Uses Google Gemini 2.5-flash for Chain-of-Thought reasoning
- Breaks down complex queries into 3 specialized sub-questions
- Coordinates the overall workflow execution
- Handles query decomposition and result consolidation

### **2. Specialized Data Agents**
- **CAPA Agent**: Processes text file data for Corrective and Preventive Actions
- **Neo4j Agent**: Queries graph database for investigation details and relationships
- **Vector Agent**: Performs similarity search on embedded clinical trial documents
- **Email Agent**: Sends consolidated summaries with human-in-the-loop approval

### **3. MCP Modules (`mcp_modules/`)**
- **mcp_capa.py**: Text file parsing and CAPA data processing
- **mcp_neo4j.py**: Graph database operations (with mock implementation)
- **mcp_vector.py**: Vector database operations (with mock implementation)  
- **mcp_email.py**: Email operations with SMTP support

### **4. Frontend (`streamlit_app.py`)**
- Streamlit-based web interface
- Real-time processing status
- Configuration panel with API status checks
- Human-in-the-loop email approval workflow

### **5. Support Systems**
- **Embeddings Handler**: Google Gemini text embeddings with fallback
- **Configuration Management**: Centralized config with environment variables
- **Logging System**: Structured logging with rotation and multiple outputs

## Data Flow

1. **Query Input**: User submits complex pharmaceutical query via Streamlit
2. **Query Breakdown**: Orchestrator uses Gemini to decompose query into 3 sub-questions
3. **Parallel Agent Execution**: 
   - CAPA Agent processes text files for compliance data
   - Neo4j Agent queries graph for investigation relationships
   - Vector Agent searches embedded clinical trial documents
4. **Result Consolidation**: Orchestrator combines all agent results
5. **Human Review**: User reviews consolidated summary in Streamlit interface
6. **Email Dispatch**: Optional email sending with user approval

## External Dependencies

### **Required APIs**
- **Google Gemini API**: Primary LLM for orchestration and embeddings
- **Neo4j Database**: Graph database for investigation relationships (mock available)
- **Astra DB/Vector Database**: Embedded document search (mock available)
- **SMTP Server**: Email delivery (mock mode available)

### **Data Sources**
- **CAPA Data File**: Tab-separated text file with compliance actions
- **Neo4j Graph**: Pre-loaded with Investigation-CAPA-Brand relationships
- **Vector Database**: Pre-embedded clinical trial PDFs and summaries

### **Python Dependencies**
- **LangGraph**: Workflow orchestration and state management
- **Streamlit**: Web interface framework
- **Google GenAI**: Gemini API client
- **Pandas**: Data manipulation for CAPA processing
- **Standard Libraries**: asyncio, logging, email, csv, json

## Deployment Strategy

### **Development Mode**
- Mock implementations for all external services
- Local file-based data sources
- Environment variable configuration
- Comprehensive logging for debugging

### **Production Readiness**
- Replace mock MCP modules with actual database clients
- Configure proper authentication for all external services
- Set up environment-specific configuration
- Enable proper email SMTP configuration
- Add monitoring and error tracking

### **Configuration Management**
- Environment variables for all sensitive data
- Centralized config class with validation
- Mock modes for development without external dependencies
- API status checking in the UI

### **Error Handling**
- Graceful degradation when services are unavailable
- Comprehensive logging at all levels
- User-friendly error messages in Streamlit
- Fallback mechanisms for critical operations

The system is designed to be highly modular and extensible, with clear separation between the orchestration layer, specialized agents, and data access patterns. The FastMCP architecture provides a consistent interface for different backends while allowing for easy development with mock implementations.

## Code Flow Documentation

### **Visual Architecture Documentation**
- **Created**: Comprehensive code flow diagram (`code_flow_diagram.html`)
- **Coverage**: Complete system architecture visualization including:
  - Overall system architecture with all layers
  - LangGraph workflow execution flow 
  - Detailed component relationships
  - File structure and dependencies
  - Technology stack integration
  - Step-by-step data flow process

### **Interactive Diagram Features**
- **Mermaid.js Integration**: Professional interactive diagrams
- **Multi-layered Views**: Architecture, workflow, components, and file structure
- **Color-coded Components**: Visual distinction between system layers
- **Detailed Process Flow**: 9-step breakdown of query processing
- **Technology Stack Mapping**: Complete dependency visualization

The diagram serves as comprehensive documentation for understanding the multi-agent system's architecture, data flow, and component interactions.