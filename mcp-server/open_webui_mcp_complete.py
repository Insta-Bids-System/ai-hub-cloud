#!/usr/bin/env python3
"""
InstaBids AI Hub - HTTP MCP Server
Simple HTTP server exposing MCP functionality for cloud deployment
"""

import asyncio
import aiohttp
import json
import os
import redis
from aiohttp import web
from typing import Dict, Any, List, Optional
from datetime import datetime

# Configuration
API_KEY = os.getenv("OPENWEBUI_API_KEY", "sk-317cb964a8a7473f9479d54fe946ea0f")
BASE_URL = os.getenv("OPENWEBUI_URL", "http://open-webui:8080")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
PORT = int(os.getenv("MCPO_PORT", "8888"))

# Initialize components
redis_client = None
session = None

def get_redis_client():
    """Get Redis client with connection pooling"""
    global redis_client
    if redis_client is None:
        try:
            redis_client = redis.from_url(REDIS_URL, decode_responses=True)
            redis_client.ping()  # Test connection
        except Exception as e:
            print(f"⚠️  Redis connection failed: {e}")
            redis_client = None
    return redis_client

async def get_session():
    """Get aiohttp session with auth headers"""
    global session
    if session is None:
        session = aiohttp.ClientSession(
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            timeout=aiohttp.ClientTimeout(total=30)
        )
    return session

async def api_request(method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
    """Make API request to Open WebUI"""
    session = await get_session()
    url = f"{BASE_URL}{endpoint}"
    
    try:
        async with session.request(method, url, json=data) as response:
            if response.content_type == 'application/json':
                result = await response.json()
            else:
                result = {"text": await response.text()}
            
            return {"status": response.status, "data": result, "success": response.status < 400}
    except Exception as e:
        return {"status": 500, "data": {"error": str(e)}, "success": False}

# HTTP Handlers
async def health_check(request):
    """Health check endpoint for DigitalOcean"""
    redis = get_redis_client()
    redis_status = "connected" if redis else "disconnected"
    
    return web.json_response({
        "status": "healthy",
        "service": "InstaBids AI Hub",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "redis": redis_status,
        "port": PORT
    })

async def mcp_tools(request):
    """Return available MCP tools"""
    tools = [
        {
            "name": "create_workspace",
            "description": "Create complete AI workspace with model and prompt",
            "inputSchema": {
                "type": "object", 
                "properties": {
                    "name": {"type": "string"}, 
                    "model": {"type": "string"}, 
                    "system_prompt": {"type": "string"}
                }, 
                "required": ["name", "model", "system_prompt"]
            }
        },
        {
            "name": "create_instabids_mobile_workspace",
            "description": "Create InstaBids mobile development workspace",
            "inputSchema": {"type": "object", "properties": {}}
        },
        {
            "name": "create_instabridge_api_workspace", 
            "description": "Create InstaBridge API development workspace",
            "inputSchema": {"type": "object", "properties": {}}
        },
        {
            "name": "create_general_dev_workspace",
            "description": "Create general development workspace", 
            "inputSchema": {
                "type": "object", 
                "properties": {"project_name": {"type": "string"}}, 
                "required": ["project_name"]
            }
        },
        {
            "name": "workspace_list",
            "description": "List all created workspaces",
            "inputSchema": {"type": "object", "properties": {}}
        },
        {
            "name": "chat_completions",
            "description": "Main chat completion endpoint", 
            "inputSchema": {
                "type": "object", 
                "properties": {
                    "model": {"type": "string"}, 
                    "messages": {"type": "array"}
                }, 
                "required": ["model", "messages"]
            }
        },
        {
            "name": "chats_list",
            "description": "List user chats",
            "inputSchema": {"type": "object", "properties": {"limit": {"type": "integer"}}}
        },
        {
            "name": "models_list",
            "description": "List all available models",
            "inputSchema": {"type": "object", "properties": {}}
        }
    ]
    
    return web.json_response({"tools": tools, "count": len(tools)})

async def mcp_call_tool(request):
    """Handle tool calls"""
    try:
        data = await request.json()
        tool_name = data.get("name")
        args = data.get("arguments", {})
        
        # Log tool usage to Redis
        redis = get_redis_client()
        if redis:
            try:
                redis.hincrby("ai-hub:tool_usage", tool_name, 1)
            except:
                pass  # Non-critical
        
        # Handle different tools
        if tool_name == "create_workspace":
            result = await create_complete_workspace(args)
        elif tool_name == "create_instabids_mobile_workspace":
            result = await create_instabids_mobile_workspace()
        elif tool_name == "create_instabridge_api_workspace":
            result = await create_instabridge_api_workspace()
        elif tool_name == "create_general_dev_workspace":
            result = await create_general_dev_workspace(args.get("project_name", "New Project"))
        elif tool_name == "workspace_list":
            result = await list_all_workspaces()
        elif tool_name == "chat_completions":
            result = await api_request("POST", "/api/chat/completions", args)
        elif tool_name == "chats_list":
            result = await api_request("GET", "/api/v1/chats/list")
        elif tool_name == "models_list":
            result = await api_request("GET", "/api/models")
        else:
            result = {"error": f"Tool not implemented: {tool_name}"}
        
        return web.json_response({"result": result})
        
    except Exception as e:
        return web.json_response({"error": str(e)}, status=400)

# Workspace creation functions
async def create_complete_workspace(args: Dict) -> Dict:
    """Create a complete AI workspace"""
    name = args.get("name", "New Workspace")
    model = args.get("model", "gpt-4")
    system_prompt = args.get("system_prompt", "You are a helpful AI assistant.")
    
    chat_data = {
        "chat": {
            "title": name,
            "messages": [{"role": "system", "content": system_prompt}],
            "models": [model],
            "tags": ["workspace", "created-by-mcp"]
        }
    }
    
    result = await api_request("POST", "/api/v1/chats/new", chat_data)
    
    if result.get("success"):
        return {"message": f"✅ Workspace '{name}' created successfully!", "success": True}
    else:
        return {"message": "❌ Failed to create workspace", "success": False}

async def create_instabids_mobile_workspace() -> Dict:
    """Create InstaBids mobile development workspace"""
    system_prompt = """You are an expert React Native developer for InstaBids mobile app.
Tech: React Native, Expo, TypeScript, NativeWind, Zustand
Colors: #1E40AF (primary), #F59E0B (secondary)"""
    
    return await create_complete_workspace({
        "name": "InstaBids Mobile Developer",
        "model": "gpt-4",
        "system_prompt": system_prompt
    })

async def create_instabridge_api_workspace() -> Dict:
    """Create InstaBridge API development workspace"""
    system_prompt = """You are a backend API expert for InstaBridge platform.
Tech: Node.js, TypeScript, Express, PostgreSQL
Focus: API design, security, integrations"""
    
    return await create_complete_workspace({
        "name": "InstaBridge API Developer",
        "model": "gpt-4",
        "system_prompt": system_prompt
    })

async def create_general_dev_workspace(project_name: str) -> Dict:
    """Create general development workspace"""
    system_prompt = f"""You are a full-stack developer for {project_name}.
Follow InstaBids standards and patterns."""
    
    return await create_complete_workspace({
        "name": f"{project_name} Developer",
        "model": "gpt-4",
        "system_prompt": system_prompt
    })

async def list_all_workspaces() -> Dict:
    """List all created workspaces"""
    result = await api_request("GET", "/api/v1/chats/list")
    
    if result.get("success"):
        chats = result.get("data", [])
        workspaces = [chat for chat in chats if "workspace" in chat.get("tags", [])]
        
        workspace_list = [
            {"id": chat.get("id", "")[:8] + "...", "title": chat.get("title", "")}
            for chat in workspaces
        ]
        
        return {
            "message": f"📋 Found {len(workspaces)} workspaces",
            "workspaces": workspace_list,
            "success": True
        }
    else:
        return {"message": "❌ Failed to list workspaces", "success": False}

async def cleanup():
    """Cleanup on shutdown"""
    global session, redis_client
    if session:
        await session.close()
    if redis_client:
        redis_client.close()

async def main():
    """Run the HTTP MCP server"""
    app = web.Application()
    
    # Routes
    app.router.add_get('/', health_check)
    app.router.add_get('/health', health_check)
    app.router.add_get('/mcp/tools', mcp_tools)
    app.router.add_post('/mcp/call', mcp_call_tool)
    
    # Set Redis status
    redis = get_redis_client()
    if redis:
        try:
            redis.set("ai-hub:mcp_server:status", "running")
            redis.set("ai-hub:mcp_server:start_time", datetime.now().isoformat())
        except:
            pass
    
    print(f"🚀 Starting InstaBids AI Hub on port {PORT}")
    print(f"🔗 Health Check: http://localhost:{PORT}/health")
    print(f"🛠️  MCP Tools: http://localhost:{PORT}/mcp/tools")
    print(f"⚡ MCP Call: http://localhost:{PORT}/mcp/call")
    
    # Start server
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    
    print(f"✅ Server running on http://0.0.0.0:{PORT}")
    
    # Keep server running with heartbeat
    try:
        while True:
            await asyncio.sleep(30)
            if redis:
                try:
                    redis.set("ai-hub:mcp_server:heartbeat", datetime.now().isoformat())
                except:
                    pass
            print(f"💓 Heartbeat: {datetime.now().strftime('%H:%M:%S')}")
            
    except KeyboardInterrupt:
        print("🛑 Shutting down...")
    finally:
        await cleanup()
        await runner.cleanup()

if __name__ == "__main__":
    asyncio.run(main())