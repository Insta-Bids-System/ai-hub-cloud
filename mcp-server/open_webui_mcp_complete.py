#!/usr/bin/env python3
"""
InstaBids AI Hub - HTTP MCP Server
FIXED: Simplified Redis connection matching MCP tools pattern
"""

import asyncio
import aiohttp
import json
import os
import redis
import ssl
import logging
from aiohttp import web
from typing import Dict, Any, List, Optional
from datetime import datetime
from urllib.parse import urlparse

# Enhanced logging configuration
logging.basicConfig(
    level=logging.DEBUG, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
API_KEY = os.getenv("OPENWEBUI_API_KEY", "sk-317cb964a8a7473f9479d54fe946ea0f")
BASE_URL = os.getenv("OPENWEBUI_URL", "http://open-webui:8080")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
PORT = int(os.getenv("MCPO_PORT", "8888"))

# Initialize components
redis_client = None
session = None

def get_redis_client():
    """Simplified Redis client matching MCP tools successful pattern"""
    global redis_client
    if redis_client is None:
        redis_url = REDIS_URL
        logger.info("🔍 Starting SIMPLIFIED Redis connection (matching MCP pattern)...")
        logger.info(f"📋 Redis URL: {redis_url[:20]}...{redis_url[-10:]}")
        
        # Parse URL for debugging
        try:
            parsed = urlparse(redis_url)
            logger.info(f"📊 Parsed URL - Host: {parsed.hostname}, Port: {parsed.port}, SSL: {parsed.scheme == 'rediss'}")
        except Exception as e:
            logger.error(f"❌ URL parsing failed: {e}")
        
        # Strategy 1: Basic SSL connection (matching MCP tools)
        try:
            logger.info("🔐 Strategy 1: Basic SSL connection (MCP pattern)...")
            redis_client = redis.from_url(
                redis_url,
                decode_responses=True,
                ssl_cert_reqs=ssl.CERT_NONE,
                ssl_check_hostname=False
            )
            
            # Test connection
            redis_client.ping()
            logger.info("✅ Strategy 1 SUCCESS: Basic SSL connection established!")
            
            # Test basic operations to match MCP success
            test_key = "ai-hub:python:connection-test"
            redis_client.set(test_key, "python-connection-working", ex=60)
            test_result = redis_client.get(test_key)
            logger.info(f"✅ Redis operations test: {test_result}")
            
            return redis_client
            
        except Exception as e:
            logger.error(f"❌ Strategy 1 FAILED: {type(e).__name__}: {e}")
            redis_client = None
        
        # Strategy 2: Even simpler SSL connection
        try:
            logger.info("🔐 Strategy 2: Minimal SSL connection...")
            redis_client = redis.from_url(redis_url, decode_responses=True)
            redis_client.ping()
            logger.info("✅ Strategy 2 SUCCESS: Minimal SSL connection established!")
            return redis_client
            
        except Exception as e:
            logger.error(f"❌ Strategy 2 FAILED: {type(e).__name__}: {e}")
            redis_client = None
        
        # Strategy 3: Direct connection with explicit SSL
        try:
            logger.info("🔐 Strategy 3: Direct SSL connection...")
            parsed = urlparse(redis_url)
            
            # Create connection pool manually
            redis_client = redis.Redis(
                host=parsed.hostname,
                port=parsed.port,
                password=parsed.password,
                username=parsed.username or 'default',
                ssl=True,
                ssl_cert_reqs=ssl.CERT_NONE,
                ssl_check_hostname=False,
                decode_responses=True
            )
            
            redis_client.ping()
            logger.info("✅ Strategy 3 SUCCESS: Direct SSL connection established!")
            return redis_client
            
        except Exception as e:
            logger.error(f"❌ Strategy 3 FAILED: {type(e).__name__}: {e}")
            redis_client = None
        
        # Strategy 4: Non-SSL fallback (last resort)
        try:
            logger.info("🔓 Strategy 4: Non-SSL fallback...")
            non_ssl_url = redis_url.replace('rediss://', 'redis://')
            logger.info(f"📋 Non-SSL URL: {non_ssl_url[:20]}...{non_ssl_url[-10:]}")
            
            redis_client = redis.from_url(non_ssl_url, decode_responses=True)
            redis_client.ping()
            logger.info("✅ Strategy 4 SUCCESS: Non-SSL connection established!")
            return redis_client
            
        except Exception as e:
            logger.error(f"❌ Strategy 4 FAILED: {type(e).__name__}: {e}")
            redis_client = None
        
        # All strategies failed
        logger.error("🚨 ALL CONNECTION STRATEGIES FAILED!")
        logger.error("📊 Environment Variables Diagnostic:")
        logger.error(f"   REDIS_URL: {'SET (' + str(len(REDIS_URL)) + ' chars)' if REDIS_URL else 'MISSING'}")
        logger.error(f"   PORT: {os.getenv('PORT', 'MISSING')}")
        
        return None
    
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
    """Enhanced health check endpoint with Redis diagnostics"""
    redis = get_redis_client()
    
    # Redis connection status
    redis_status = "disconnected"
    redis_details = {}
    
    if redis:
        try:
            # Test basic ping
            ping_result = redis.ping()
            redis_status = "connected"
            
            # Get Redis info
            redis_info = redis.info()
            redis_details = {
                "ping": ping_result,
                "version": redis_info.get('redis_version', 'unknown'),
                "server_name": redis_info.get('server_name', 'redis'),
                "connected_clients": redis_info.get('connected_clients', 0),
                "used_memory_human": redis_info.get('used_memory_human', 'unknown'),
                "uptime_in_seconds": redis_info.get('uptime_in_seconds', 0)
            }
            
            # Test our app-specific keys
            try:
                app_status = redis.get("ai-hub:mcp_server:status")
                redis_details["app_status"] = app_status
                
                # Test write operation
                redis.set("ai-hub:health_check", datetime.now().isoformat(), ex=300)
                redis_details["last_health_check"] = "success"
            except Exception as e:
                redis_details["app_operations"] = f"error: {e}"
            
            logger.info(f"✅ Health check passed - Redis connected: {redis_details}")
            
        except Exception as e:
            redis_status = f"error: {str(e)}"
            redis_details = {"error": str(e)}
            logger.error(f"❌ Health check Redis error: {e}")
    else:
        logger.warning("⚠️ Health check - Redis client not available")
    
    return web.json_response({
        "status": "healthy",
        "service": "InstaBids AI Hub",
        "version": "2.1.0-simplified",
        "timestamp": datetime.now().isoformat(),
        "redis": {
            "status": redis_status,
            "details": redis_details
        },
        "port": PORT,
        "environment": os.getenv('ENVIRONMENT', 'production'),
        "deployment_id": os.getenv('DIGITALOCEAN_APP_ID', 'unknown')
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
    
    logger.info(f"📋 MCP Tools requested - returning {len(tools)} tools")
    return web.json_response({"tools": tools, "count": len(tools)})

async def mcp_call_tool(request):
    """Handle tool calls with enhanced logging"""
    try:
        data = await request.json()
        tool_name = data.get("name")
        args = data.get("arguments", {})
        
        logger.info(f"🔧 MCP Tool called: {tool_name} with args: {args}")
        
        # Log tool usage to Redis
        redis = get_redis_client()
        if redis:
            try:
                redis.hincrby("ai-hub:tool_usage", tool_name, 1)
                logger.debug(f"📊 Tool usage logged for: {tool_name}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to log tool usage: {e}")
        
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
        
        logger.info(f"✅ Tool {tool_name} completed successfully")
        return web.json_response({"result": result})
        
    except Exception as e:
        logger.error(f"❌ Tool call failed: {e}")
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
            "message": f"📊 Found {len(workspaces)} workspaces",
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
    """Run the simplified HTTP MCP server"""
    app = web.Application()
    
    # Routes
    app.router.add_get('/', health_check)
    app.router.add_get('/health', health_check)
    app.router.add_get('/mcp/tools', mcp_tools)
    app.router.add_post('/mcp/call', mcp_call_tool)
    
    # Initialize Redis connection with simplified approach
    logger.info("🚀 Starting InstaBids AI Hub SIMPLIFIED Server...")
    redis = get_redis_client()
    if redis:
        try:
            redis.set("ai-hub:mcp_server:status", "running")
            redis.set("ai-hub:mcp_server:start_time", datetime.now().isoformat())
            redis.set("ai-hub:mcp_server:version", "2.1.0-simplified")
            logger.info("🔗 Redis integration enabled successfully")
        except Exception as e:
            logger.error(f"❌ Redis init failed: {e}")
    else:
        logger.warning("📱 Running without Redis (non-critical)")
    
    logger.info(f"🌐 Starting InstaBids AI Hub on port {PORT}")
    logger.info(f"✅ Health Check: http://localhost:{PORT}/health")
    logger.info(f"🛠️ MCP Tools: http://localhost:{PORT}/mcp/tools")
    logger.info(f"⚡ MCP Call: http://localhost:{PORT}/mcp/call")
    
    # Start server
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    
    logger.info(f"✅ Server running on http://0.0.0.0:{PORT}")
    
    # Keep server running with heartbeat
    try:
        while True:
            await asyncio.sleep(30)
            if redis:
                try:
                    redis.set("ai-hub:mcp_server:heartbeat", datetime.now().isoformat())
                except:
                    pass
            logger.info(f"💓 Heartbeat: {datetime.now().strftime('%H:%M:%S')}")
            
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down...")
    finally:
        await cleanup()
        await runner.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
