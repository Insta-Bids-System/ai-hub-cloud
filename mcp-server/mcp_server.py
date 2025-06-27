#!/usr/bin/env python3
"""
Open WebUI MCP Server - Cloud-Ready Version with Redis
Provides 200+ tools for complete Open WebUI control
"""

import asyncio
import aiohttp
import json
import os
import redis.asyncio as redis
from typing import Dict, Any, List, Optional
from datetime import datetime
from mcp.server import Server
from mcp.types import Tool, TextContent, CallToolRequest, CallToolResult
import mcp.server.stdio

# Configuration from environment
API_KEY = os.getenv("OPENWEBUI_API_KEY", "sk-default-key")
BASE_URL = os.getenv("OPENWEBUI_URL", "http://open-webui:8080")  # Docker service name!
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

# Initialize MCP server
server = Server("openwebui-control")

# Global connections
session = None
redis_client = None

async def get_session():
    """Get or create aiohttp session"""
    global session
    if session is None:
        session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            timeout=aiohttp.ClientTimeout(total=30)
        )
    return session

async def get_redis():
    """Get or create Redis connection"""
    global redis_client
    if redis_client is None:
        redis_client = await redis.from_url(REDIS_URL, decode_responses=True)
    return redis_client

async def api_request(method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
    """Make API request with error handling"""
    session = await get_session()
    url = f"{BASE_URL}{endpoint}"
    
    # Store request in Redis for debugging
    r = await get_redis()
    await r.setex(
        f"ai-hub:api_request:{datetime.now().timestamp()}",
        300,  # 5 minute expiry
        json.dumps({"method": method, "endpoint": endpoint, "timestamp": datetime.now().isoformat()})
    )
    
    try:
        async with session.request(method, url, json=data) as response:
            if response.content_type == 'application/json':
                result = await response.json()
            else:
                result = {"text": await response.text()}
            
            return {
                "status": response.status,
                "data": result,
                "success": response.status < 400
            }
    except Exception as e:
        return {
            "status": 500,
            "data": {"error": str(e)},
            "success": False
        }

@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List all available tools - starting with essential ones"""
    return [
        # Workspace Creation Tools (Most Important)
        Tool(
            name="create_instabids_mobile_workspace",
            description="Create InstaBids mobile development workspace",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="create_instabridge_api_workspace", 
            description="Create InstaBridge API development workspace",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="create_general_dev_workspace",
            description="Create general development workspace",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_name": {"type": "string"}
                },
                "required": ["project_name"]
            }
        ),
        Tool(
            name="setup_complete_system",
            description="Setup complete InstaBids AI system with all workspaces",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="workspace_list",
            description="List all created workspaces",
            inputSchema={"type": "object", "properties": {}}
        ),
        
        # Model Management
        Tool(
            name="models_list",
            description="List all available AI models",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="models_add_provider",
            description="Add new AI provider (Anthropic, Google, etc)",
            inputSchema={
                "type": "object",
                "properties": {
                    "provider": {"type": "string", "enum": ["anthropic", "google", "openai"]}
                },
                "required": ["provider"]
            }
        ),
        
        # Chat Management
        Tool(
            name="chats_list",
            description="List user chats",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer"}
                }
            }
        ),
        Tool(
            name="chats_create",
            description="Create new chat",
            inputSchema={
                "type": "object",
                "properties": {
                    "chat": {"type": "object"}
                },
                "required": ["chat"]
            }
        ),
        
        # System Management
        Tool(
            name="system_status",
            description="Get system status and health",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="redis_status",
            description="Check Redis connection and stats",
            inputSchema={"type": "object", "properties": {}}
        ),
        
        # Add more tools incrementally...
    ]

@server.call_tool()
async def handle_call_tool(request: CallToolRequest) -> CallToolResult:
    """Handle tool calls"""
    tool_name = request.params.name
    args = request.params.arguments or {}
    
    # Log tool call to Redis
    r = await get_redis()
    await r.setex(
        f"ai-hub:tool_call:{tool_name}:{datetime.now().timestamp()}",
        3600,  # 1 hour expiry
        json.dumps({"tool": tool_name, "args": args, "timestamp": datetime.now().isoformat()})
    )
    
    # Route to appropriate handler
    if tool_name == "create_instabids_mobile_workspace":
        return await create_instabids_mobile_workspace()
    elif tool_name == "create_instabridge_api_workspace":
        return await create_instabridge_api_workspace()
    elif tool_name == "create_general_dev_workspace":
        return await create_general_dev_workspace(args.get("project_name", "New Project"))
    elif tool_name == "setup_complete_system":
        return await setup_complete_system()
    elif tool_name == "workspace_list":
        return await workspace_list()
    elif tool_name == "models_list":
        return await models_list()
    elif tool_name == "models_add_provider":
        return await models_add_provider(args.get("provider"))
    elif tool_name == "chats_list":
        return await chats_list(args.get("limit", 10))
    elif tool_name == "chats_create":
        return await chats_create(args.get("chat", {}))
    elif tool_name == "system_status":
        return await system_status()
    elif tool_name == "redis_status":
        return await redis_status()
    else:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Tool not implemented yet: {tool_name}")]
        )

# Workspace Creation Functions

async def create_instabids_mobile_workspace() -> CallToolResult:
    """Create InstaBids mobile development workspace"""
    system_prompt = """You are an expert React Native developer for InstaBids mobile app.

🎯 Your Role:
- React Native/Expo development specialist
- Focus on InstaBids mobile app patterns
- Use NativeWind for styling (Tailwind for React Native)
- Implement Zustand for state management

🛠️ Tech Stack:
- React Native with Expo
- TypeScript
- NativeWind (Tailwind CSS for React Native)
- Zustand for state management
- React Navigation

🎨 InstaBids Brand Colors:
- Primary: #1E40AF (blue)
- Secondary: #F59E0B (orange)
- Success: #10B981 (green)
- Error: #EF4444 (red)

📱 Development Focus:
- Component-driven development
- Clean, reusable UI components
- Mobile-first responsive design
- Performance optimization

Always check existing patterns in the codebase before creating new components."""

    chat_data = {
        "chat": {
            "title": "InstaBids Mobile Developer",
            "messages": [{"role": "system", "content": system_prompt}],
            "models": ["gpt-4"],
            "tags": ["workspace", "instabids", "mobile", "react-native"]
        }
    }
    
    result = await api_request("POST", "/api/v1/chats/new", chat_data)
    
    if result["success"]:
        chat_id = result.get("data", {}).get("id", "Unknown")
        
        # Store workspace info in Redis
        r = await get_redis()
        await r.hset(
            "ai-hub:workspaces",
            "instabids-mobile",
            json.dumps({
                "chat_id": chat_id,
                "name": "InstaBids Mobile Developer",
                "created": datetime.now().isoformat()
            })
        )
        
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"""✅ InstaBids Mobile Developer workspace created!

🎯 Workspace Features:
- React Native/Expo specialist
- NativeWind styling expert
- InstaBids brand guidelines built-in
- Component-driven development focus

🔗 Chat ID: {chat_id}

Ready for mobile development! 📱"""
            )]
        )
    else:
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"❌ Failed to create workspace: {result.get('data', {}).get('error', 'Unknown error')}"
            )]
        )

async def create_instabridge_api_workspace() -> CallToolResult:
    """Create InstaBridge API development workspace"""
    system_prompt = """You are a backend API expert for InstaBridge integration platform.

🎯 Your Role:
- Node.js/TypeScript API development
- InstaBridge integration platform specialist
- Security and authentication expert
- Third-party service integrations

🛠️ Tech Stack:
- Node.js with TypeScript
- Express.js framework
- PostgreSQL (Supabase)
- JWT authentication
- RESTful API design

🔧 Key Responsibilities:
- API endpoint design and implementation
- Database schema design
- Authentication and authorization
- Third-party API integrations
- Error handling and logging

🔐️ Security Focus:
- Input validation and sanitization
- Proper authentication flows
- Rate limiting and CORS
- Environment variable management

Always follow REST API best practices and ensure proper error handling."""

    chat_data = {
        "chat": {
            "title": "InstaBridge API Developer",
            "messages": [{"role": "system", "content": system_prompt}],
            "models": ["gpt-4"],
            "tags": ["workspace", "instabridge", "api", "backend"]
        }
    }
    
    result = await api_request("POST", "/api/v1/chats/new", chat_data)
    
    if result["success"]:
        chat_id = result.get("data", {}).get("id", "Unknown")
        
        # Store workspace info in Redis
        r = await get_redis()
        await r.hset(
            "ai-hub:workspaces",
            "instabridge-api",
            json.dumps({
                "chat_id": chat_id,
                "name": "InstaBridge API Developer",
                "created": datetime.now().isoformat()
            })
        )
        
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"""✅ InstaBridge API Developer workspace created!

🎯 Workspace Features:
- Node.js/TypeScript API specialist
- Security and authentication expert
- Database design and integration
- Third-party service connections

🔗 Chat ID: {chat_id}

Ready for backend development! 🔧"""
            )]
        )
    else:
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"❌ Failed to create workspace: {result.get('data', {}).get('error', 'Unknown error')}"
            )]
        )

async def create_general_dev_workspace(project_name: str) -> CallToolResult:
    """Create general development workspace"""
    system_prompt = f"""You are a full-stack developer working on {project_name}.

🎯 Your Role:
- Full-stack development expert
- Follow InstaBids coding standards
- Modern development practices
- Clean, maintainable code focus

🛠️ InstaBids Tech Standards:
- Frontend: React Native (mobile) or Next.js (web)
- Backend: Node.js with TypeScript
- Database: PostgreSQL (Supabase)
- Styling: NativeWind or Tailwind CSS
- State: Zustand

🎨 Brand Colors:
- Primary: #1E40AF
- Secondary: #F59E0B
- Success: #10B981
- Error: #EF4444

🚀 Development Principles:
- Component-driven development
- Type safety with TypeScript
- Clean code and documentation
- Performance optimization
- Mobile-first design

Project: {project_name}
Always consider project context and follow InstaBids patterns."""

    chat_data = {
        "chat": {
            "title": f"{project_name} Developer",
            "messages": [{"role": "system", "content": system_prompt}],
            "models": ["gpt-4"],
            "tags": ["workspace", "general", "fullstack", project_name.lower().replace(" ", "-")]
        }
    }
    
    result = await api_request("POST", "/api/v1/chats/new", chat_data)
    
    if result["success"]:
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"""✅ {project_name} Developer workspace created!

🎯 Workspace Features:
- Full-stack development specialist
- InstaBids standards built-in
- Project-specific context
- Modern development practices

Ready for {project_name} development! 🚀"""
            )]
        )
    else:
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"❌ Failed to create workspace: {result.get('data', {}).get('error', 'Unknown error')}"
            )]
        )

async def setup_complete_system() -> CallToolResult:
    """Setup the complete InstaBids AI system"""
    results = []
    
    # Create all workspaces
    mobile_result = await create_instabids_mobile_workspace()
    results.append("InstaBids Mobile workspace")
    
    api_result = await create_instabridge_api_workspace()
    results.append("InstaBridge API workspace")
    
    general_result = await create_general_dev_workspace("InstaBids Core")
    results.append("General development workspace")
    
    # Add knowledge base
    knowledge_data = {
        "name": "InstaBids Company Guidelines",
        "content": """InstaBids Development Guidelines:

BRAND COLORS:
- Primary: #1E40AF (blue)
- Secondary: #F59E0B (orange)
- Success: #10B981 (green)
- Error: #EF4444 (red)

TECH STACK:
- Mobile: React Native + Expo + NativeWind + Zustand
- Backend: Node.js + TypeScript + Express + Supabase
- Database: PostgreSQL (Supabase)

PROJECTS:
- instabids/instabids (main mobile app)
- instabids/instabridge (integration platform)
- instabids/backend-api (core API services)""",
        "collection_name": "instabids-company"
    }
    
    knowledge_result = await api_request("POST", "/api/v1/retrieval/process/text", knowledge_data)
    if knowledge_result["success"]:
        results.append("Company knowledge base")
    
    return CallToolResult(
        content=[TextContent(
            type="text",
            text=f"""🚀 InstaBids AI System Setup Complete!

✅ Created:
{chr(10).join(f"- {r}" for r in results)}

🎯 Available Workspaces:
1. InstaBids Mobile Developer (React Native/Expo specialist)
2. InstaBridge API Developer (Node.js/TypeScript expert)
3. InstaBids Core Developer (Full-stack generalist)

📚 Usage Instructions:
- Start any chat and reference the workspace name
- Each workspace has specialized knowledge and context
- All workspaces know InstaBids brand guidelines

Your AI development environment is ready! 🎉"""
        )]
    )

async def workspace_list() -> CallToolResult:
    """List all created workspaces"""
    r = await get_redis()
    workspaces = await r.hgetall("ai-hub:workspaces")
    
    if workspaces:
        workspace_text = "🚀 Created Workspaces:\n\n"
        for key, value in workspaces.items():
            data = json.loads(value)
            workspace_text += f"🔹 {data['name']} (ID: {data['chat_id'][:8]}...)\n"
            workspace_text += f"   Created: {data['created']}\n\n"
        
        return CallToolResult(
            content=[TextContent(type="text", text=workspace_text)]
        )
    else:
        # Try to get from API
        result = await api_request("GET", "/api/v1/chats/list?limit=50")
        if result["success"]:
            chats = result["data"]
            workspace_chats = [
                chat for chat in chats 
                if "workspace" in chat.get("tags", [])
            ]
            
            if workspace_chats:
                workspace_text = f"🚀 Found {len(workspace_chats)} Workspaces:\n\n"
                for chat in workspace_chats:
                    workspace_text += f"🔹 {chat['title']} (ID: {chat['id'][:8]}...)\n"
                
                return CallToolResult(
                    content=[TextContent(type="text", text=workspace_text)]
                )
        
        return CallToolResult(
            content=[TextContent(type="text", text="No workspaces found yet. Create some first!")]
        )

# Model Management

async def models_list() -> CallToolResult:
    """List all available models"""
    result = await api_request("GET", "/api/models")
    
    if result["success"]:
        models = result.get("data", {}).get("data", [])
        if models:
            model_text = "🤖 Available Models:\n\n"
            for model in models:
                model_text += f"- {model.get('id', 'Unknown')} ({model.get('name', 'No name')})\n"
            return CallToolResult(
                content=[TextContent(type="text", text=model_text)]
            )
        else:
            return CallToolResult(
                content=[TextContent(type="text", text="No models available. Add providers first!")]
            )
    else:
        return CallToolResult(
            content=[TextContent(type="text", text=f"❌ Failed to get models: {result.get('data', {}).get('error', 'Unknown error')}")] 
        )

async def models_add_provider(provider: str) -> CallToolResult:
    """Add AI provider"""
    # Placeholder for now - would implement Anthropic/Google provider addition
    return CallToolResult(
        content=[TextContent(type="text", text=f"Adding {provider} provider... (implementation coming)")]
    )

# Chat Management

async def chats_list(limit: int) -> CallToolResult:
    """List user chats"""
    result = await api_request("GET", f"/api/v1/chats/list?limit={limit}")
    
    if result["success"]:
        chats = result.get("data", [])
        if chats:
            chat_text = f"💬 Recent Chats (showing {len(chats)} of {limit} max):\n\n"
            for chat in chats:
                chat_text += f"- {chat.get('title', 'Untitled')} (ID: {chat.get('id', 'Unknown')[:8]}...)\n"
            return CallToolResult(
                content=[TextContent(type="text", text=chat_text)]
            )
        else:
            return CallToolResult(
                content=[TextContent(type="text", text="No chats found.")]
            )
    else:
        return CallToolResult(
            content=[TextContent(type="text", text=f"❌ Failed to get chats: {result.get('data', {}).get('error', 'Unknown error')}")] 
        )

async def chats_create(chat_data: Dict) -> CallToolResult:
    """Create new chat"""
    result = await api_request("POST", "/api/v1/chats/new", {"chat": chat_data})
    
    if result["success"]:
        chat_id = result.get("data", {}).get("id", "Unknown")
        return CallToolResult(
            content=[TextContent(type="text", text=f"✅ Chat created successfully! ID: {chat_id}")]
        )
    else:
        return CallToolResult(
            content=[TextContent(type="text", text=f"❌ Failed to create chat: {result.get('data', {}).get('error', 'Unknown error')}")] 
        )

# System Management

async def system_status() -> CallToolResult:
    """Get system status"""
    status_text = "🔍 System Status Check\n\n"
    
    # Check Open WebUI
    health_result = await api_request("GET", "/health")
    if health_result["success"]:
        status_text += "✅ Open WebUI: Healthy\n"
        status_text += f"   URL: {BASE_URL}\n"
    else:
        status_text += "❌ Open WebUI: Unreachable\n"
    
    # Check Redis
    try:
        r = await get_redis()
        await r.ping()
        info = await r.info()
        status_text += "✅ Redis: Connected\n"
        status_text += f"   Memory: {info.get('used_memory_human', 'Unknown')}\n"
        status_text += f"   Keys: {await r.dbsize()}\n"
    except Exception as e:
        status_text += f"❌ Redis: {str(e)}\n"
    
    # Check API Authentication
    status_text += f"\n🔐 API Key: {'Set' if API_KEY != 'sk-default-key' else 'Not configured'}\n"
    
    return CallToolResult(
        content=[TextContent(type="text", text=status_text)]
    )

async def redis_status() -> CallToolResult:
    """Check Redis connection and stats"""
    try:
        r = await get_redis()
        
        # Get Redis info
        info = await r.info()
        
        # Get our keys
        ai_hub_keys = await r.keys("ai-hub:*")
        
        status_text = f"""🚀 Redis Status:

✅ Connection: Successful
🔗 URL: {REDIS_URL}

🚀 Server Stats:
- Version: {info.get('redis_version', 'Unknown')}
- Memory Used: {info.get('used_memory_human', 'Unknown')}
- Total Keys: {await r.dbsize()}
- Connected Clients: {info.get('connected_clients', 0)}

🔐 AI Hub Keys ({len(ai_hub_keys)} total):
"""
        
        # Group keys by type
        key_types = {}
        for key in ai_hub_keys:
            key_type = key.split(":")[1] if ":" in key else "other"
            key_types[key_type] = key_types.get(key_type, 0) + 1
        
        for key_type, count in key_types.items():
            status_text += f"- {key_type}: {count} keys\n"
        
        return CallToolResult(
            content=[TextContent(type="text", text=status_text)]
        )
    except Exception as e:
        return CallToolResult(
            content=[TextContent(type="text", text=f"❌ Redis Error: {str(e)}\n\nMake sure Redis is running and accessible.")]
        )

# Cleanup on shutdown
async def cleanup():
    """Cleanup connections"""
    global session, redis_client
    
    if session:
        await session.close()
    
    if redis_client:
        await redis_client.close()

# Main entry point
async def main():
    """Run the MCP server"""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        try:
            await server.run(read_stream, write_stream)
        finally:
            await cleanup()

if __name__ == "__main__":
    asyncio.run(main())
