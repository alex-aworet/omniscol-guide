# Omniscol Guide - Intelligent Onboarding Platform

## 📋 Project Overview

**Omniscol Guide** is an intelligent AI-powered onboarding assistant for the Omniscol school management platform. This system combines advanced artificial intelligence with comprehensive platform documentation to provide real-time, context-aware guidance to users navigating the school administration system.

The project bridges the gap between complex school management software and its users by leveraging modern LLM (Large Language Model) technology to deliver personalized, intelligent assistance that understands both the platform structure and user intent.

---

## 🎯 Core Purpose

The primary objectives of Omniscol Guide are:

1. **Intelligent User Guidance**: Provide AI-assisted explanations and step-by-step instructions for navigating complex school management tasks
2. **Context Awareness**: Understand the user's current location within the platform and provide relevant assistance
3. **Natural Language Interaction**: Allow users to ask questions in natural language and receive precise, actionable answers
4. **Knowledge Management**: Maintain a comprehensive database (site_map.json) of all platform features, sections, and workflows
5. **Real-time Support**: Deliver instant assistance without requiring manual documentation lookup

---

## 🛠 Technology Stack

### Backend & Core Technologies

- **FastAPI** (v0.135.2) - High-performance Python web framework for building REST APIs and WebSocket support
- **Python 3.x** - Primary programming language
- **Socket.IO** (v5.16.1) - Real-time bidirectional communication between client and server
- **Uvicorn** (v0.42.0) - ASGI web server for running FastAPI applications
- **Starlette** (v1.0.0) - Lightweight ASGI framework underlying FastAPI

### AI & LLM Integration

- **Ollama** (v0.6.1) - Local LLM inference engine for running language models
- **MCP (Model Context Protocol)** (v1.26.0) - Protocol for standardized AI tool integration and communication
- **Pydantic** (v2.12.5) - Data validation and serialization using Python type annotations

### Web Technologies

- **CORS Middleware** - Cross-Origin Resource Sharing for secure cross-domain requests
- **HTTP Server** - Simple Python HTTP server for static file serving (server.py)
- **CSS/JavaScript Frameworks** - Client-side UI components and styling (guide.js, guide-chat.css)

### Additional Dependencies

- **Playwright** (v1.58.0) - Browser automation for web scraping and testing
- **HTTPx** (v0.28.1) - Modern HTTP client for async requests
- **PyYAML** (v6.0.3) - Configuration file parsing
- **python-dotenv** (v1.2.2) - Environment variable management
- **Watchfiles** (v1.1.1) - File change detection for development

---

## 🏗 Architecture & Design Strategies

### 1. **Model Context Protocol (MCP) Architecture**

The project implements the Model Context Protocol to create a standardized interface between AI models and platform tools:

- **MCP Server** (`guide/mcp_server.py`): Exposes structured tools and data to AI models
- **MCP Tools**: Predefined functions that the AI can call to access platform information
- **Tool Conversion**: Automatic conversion of MCP tools to Ollama function-calling format

**Key MCP Tools:**
- `list_tabs()` - Retrieve all available tabs in the platform
- `get_tab_by_route()` - Find a specific tab by its URL route
- `get_tab_context()` - Get detailed information about a tab and its sections
- `search_ui()` - Full-text search across all platform UI elements
- `check_route_match()` - Compare two routes to determine current location

### 2. **Knowledge Graph Strategy**

The project uses a JSON-based knowledge graph (`guide/site_map.json`) as the central information hub:

```json
{
  "tabs": [
    {
      "id": "home",
      "title": "Home",
      "description": "Platform homepage",
      "route": "/",
      "sections": [...]
    }
  ]
}
```

**Benefits:**
- Centralized, maintainable documentation
- Machine-readable platform structure
- Enables efficient search and context retrieval
- Decoupled from implementation code

### 3. **Context-Aware AI Agent**

The `GuideAgent` class (`guide/agent.py`) implements intelligent reasoning with page context:

**Strategy:** The agent receives:
- Current route (URL path)
- Active tab information
- Visible page sections
- User question

**Process:**
1. Route comparison to determine user's current location
2. Contextual information gathering using MCP tools
3. LLM reasoning with access to full platform knowledge
4. Answer generation with route-specific guidance

**Critical Instructions for AI:**
- Use available tools immediately for accurate information
- Never fabricate UI elements not in the documentation
- Provide confident, direct answers based on site_map data
- Avoid repeating internal metadata in responses

### 4. **Dual Server Architecture**

Two complementary server implementations provide flexibility:

**Option A: FastAPI Server (`main.py`)**
- Full-featured API with WebSocket support
- Production-ready with proper CORS handling
- Includes Socket.IO for real-time communication
- Advanced middleware configuration

**Option B: Simple HTTP Server (`server.py`)**
- Lightweight Python HTTP server
- Minimal dependencies
- Quick prototyping and development
- CORS support for cross-origin requests
- JSON response handling for API endpoints

### 5. **Real-time Communication Strategy**

WebSocket and Socket.IO integration enables:
- Live connection between client and server
- Instant AI response delivery
- Bidirectional event-driven architecture
- Connection health monitoring (ping/pong)
- Scalable concurrent connections

### 6. **Frontend Integration Pattern**

The guide is integrated into the web interface through:

- **Guide Chat Module** (`webapp/js/guide.js`) - Main chat interface
- **CSS Styling** (`webapp/css/guide-chat.css`) - Chat UI styling
- **Event Listeners** - JavaScript hooks for page context detection
- **Route Detection** - Automatic capture of current page location
- **Component Library** - Shared UI components across the platform

---

## 📁 Project Structure

```
omniscol-guide/
├── index.html              # Entry point - platform homepage
├── server.py               # Simple HTTP server for quick setup
├── main.py                 # FastAPI application (production)
├── requirements.txt        # Python dependencies
├── start.sh                # Shell script for easy startup

├── guide/                  # Core AI guidance system
│   ├── agent.py           # Main AI agent implementation
│   ├── mcp_server.py      # MCP protocol server exposing tools
│   ├── site_map.json      # Knowledge graph (1511 lines - comprehensive!)
│   ├── capture_tabs_simple.py # Script for capturing UI structure
│   ├── providers/
│   │   └── ollama_adapter.py  # Ollama LLM integration
│   └── screenshots/       # UI element screenshots for reference

├── api/                    # API endpoints documentation
│   ├── home.html
│   ├── guest/endpoints.html
│   └── schedules/lessons/

├── webapp/                 # Frontend application
│   ├── js/                # JavaScript modules
│   │   ├── guide.js              # Main guide interface
│   │   ├── dashboard.min.js
│   │   ├── admin.min.js
│   │   └── [other modules]
│   └── css/               # Stylesheets
│       ├── guide-chat.css        # Guide UI styling
│       └── [other styles]

├── core/                  # Core platform assets
│   ├── css/core.min.css
│   └── js/core.min.js

├── public/                # Public assets
│   ├── fonts/fontawesome/
│   └── js/pace.min.js

└── tests/                 # Test suite
    └── unit/
```

---

## 🔄 Data Flow & Process

### Request Processing Flow

```
User Question
    ↓
JavaScript Event (guide.js)
    ↓
WebSocket/HTTP Connection to Server
    ↓
FastAPI/HTTP Server Routes Request
    ↓
GuideAgent Receives Query + Page Context
    ↓
MCP Client Queries Tools
    ↓
MCP Server (mcp_server.py) Accesses site_map.json
    ↓
Tools Return UI Structure & Metadata
    ↓
Ollama Adapter Prepares Tools for LLM
    ↓
Local LLM (via Ollama) Generates Answer
    ↓
Response Sent Back Through WebSocket
    ↓
Guide Chat UI Displays Answer to User
```

### Key Data Structures

**Page Context Object:**
```python
{
    "route": "/dashboard/teachers",      # Current URL path
    "active_tab": "teachers",            # Active section
    "visible_sections": ["chart", ...]   # Visible UI elements
}
```

**Tool Result from MCP:**
```python
{
    "type": "tab" | "section",
    "route": "/path",
    "title": "Feature Title",
    "description": "Feature description",
    "id": "feature_id"
}
```

---

## 🚀 Key Features & Capabilities

### 1. **Intelligent Search**
- Full-text search across tabs and sections
- Route-aware matching
- Relevance ranking

### 2. **Route Matching**
- Exact route comparison
- Current location detection
- Contextual guidance based on position

### 3. **Context Preservation**
- Maintains conversation context
- Understands user's current page
- Provides page-specific instructions

### 4. **Safe AI Responses**
- Prevents AI hallucination about features
- Only describes documented platform elements
- Gracefully handles unknown features
- Honest about missing information

### 5. **Multi-Tab Support**
- Supports complex multi-tab interfaces
- Section-level granularity
- Deep platform documentation

---

## 🧠 AI Strategy & Prompt Engineering

The system employs sophisticated prompt engineering to ensure reliable AI behavior:

### System Prompt Principles

1. **Knowledge Source**: "You have complete knowledge of the platform structure through the site_map.json database"
2. **Confidence**: "Always provide DIRECT, CONFIDENT answers based on the site_map data"
3. **Tool Usage**: "Use available tools IMMEDIATELY for any question"
4. **Truth Constraint**: "NEVER FABRICATE UI elements that do not appear in search results"
5. **Honesty**: "If not found in search results, say honestly that you could not find it"

### Route Matching Logic

```
1. User's current route (definitive)
   ↓
2. Search for requested feature
   ↓
3. Compare result_route == current_route
   ↓
4. If match: Feature is on current page
   If no match: Provide navigation instructions
```

---

## 🔧 Getting Started

### Prerequisites
- Python 3.8+
- Ollama installed and running (for AI features)
- pip (Python package manager)

### Installation

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Option A - Simple Server (Quick Setup):**
   ```bash
   python3 server.py
   ```
   Access at: `http://localhost:8001`

3. **Option B - FastAPI Server (Full Features):**
   ```bash
   python3 main.py
   ```
   Access at: `http://localhost:8000`

4. **Or Use the Startup Script:**
   ```bash
   chmod +x start.sh
   ./start.sh
   ```

### Configuration

- **Port**: Modify `PORT` variable in `server.py` or `main.py`
- **CORS**: Configure allowed origins in FastAPI middleware
- **LLM Model**: Set via `OllamaAdapter` configuration
- **Environment**: Use `.env` file for configuration variables

---

## 📊 Knowledge Base (site_map.json)

The site_map.json file is the heart of the system:

- **Format**: JSON with hierarchical structure
- **Size**: 1511 lines of comprehensive platform documentation
- **Content**: Tabs, sections, routes, descriptions, selectors
- **Scope**: Covers all major platform features:
  - Home Dashboard
  - Teacher Management
  - Course Scheduling
  - Absence Tracking
  - Timetable Management
  - Administration Panel
  - And many more...

### Usage Pattern
```python
# Tools automatically query this file
list_tabs()           # Returns all 30+ tabs
search_ui("teachers") # Finds teacher-related sections
get_tab_by_route("/dashboard/teachers")  # Route lookup
```

---

## 🎓 Use Cases

1. **Student Onboarding**: New users get step-by-step guidance
2. **Feature Discovery**: "How do I manage absences?"
3. **Navigation Help**: "Where can I find the timetable?"
4. **Workflow Assistance**: "What's the process for scheduling courses?"
5. **Admin Support**: "How do I configure the system?"

---

## 🔐 Security Considerations

- CORS properly configured to prevent unauthorized access
- Environment variables for sensitive data (via python-dotenv)
- Local LLM execution (no external API calls by default)
- Static file serving with proper path handling
- Socket.IO with configurable origins

---

## 📈 Development & Extension

### Adding New Features to the Guide

1. **Update site_map.json**: Add new tab/section entries
2. **Define MCP Tool**: Create tool in mcp_server.py if needed
3. **Update Frontend**: Add UI elements to webapp/
4. **Test**: Verify through guide.js integration

### Extending the AI Agent

1. Modify system prompt in `agent.py`
2. Add new tools in `mcp_server.py`
3. Configure new tool parameters
4. Test with various queries

---

## 📝 Notes

- The project uses async/await for high-concurrency support
- Socket.IO connections include health monitoring (ping/pong)
- Client-side guide.js automatically detects page context
- All AI responses are grounded in documented platform structure

---

## 🤝 Support & Maintenance

- Check logs in terminal for debugging
- Verify Ollama is running for AI features
- Port conflicts? Modify PORT variable
- CORS issues? Check middleware configuration
- Static files not loading? Verify server working directory

---

## 📜 License & Attribution

This project combines:
- **FastAPI/Starlette**: Modern Python async web framework
- **Model Context Protocol**: Anthropic's standardized AI tool protocol
- **Ollama**: Open-source LLM inference
- **Omniscol Platform**: Educational institution management system

---

## 🎯 Future Enhancements

Potential expansion areas:
- Multi-language support for internationalization
- Advanced analytics tracking user questions
- Feedback loop to improve knowledge base
- Integration with external documentation systems
- Mobile app companion
- Video tutorial generation from site_map data
- Automated UI change detection
- Multi-model LLM support

---

**Version**: 1.0.0  
**Last Updated**: 2026  
**Project Status**: Active Development
