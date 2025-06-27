#!/usr/bin/env python3
"""
InstaBids AI Hub - HTTP MCP Server
FIXED: Valkey 8.0.3 URL Query Parameter Solution (Context7 Research) + Frontend UI
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
    """VALKEY 8.0.3 URL QUERY PARAMETER FIX - Based on Context7 research"""
    global redis_client
    if redis_client is None:
        base_redis_url = REDIS_URL
        logger.info("🎯 IMPLEMENTING VALKEY 8.0.3 URL QUERY PARAMETER FIX...")
        logger.info(f"📋 Base Redis URL: {base_redis_url[:20]}...{base_redis_url[-10:]}")
        
        # Parse URL for debugging
        try:
            parsed = urlparse(base_redis_url)
            logger.info(f"📋 Parsed URL - Host: {parsed.hostname}, Port: {parsed.port}, SSL: {parsed.scheme == 'rediss'}")
        except Exception as e:
            logger.error(f"❌ URL parsing failed: {e}")
        
        # Strategy 1: URL Query Parameters (CORRECT for Valkey 8.0.3)
        try:
            logger.info("🎯 Strategy 1: URL query parameters (Valkey-compatible)...")
            redis_url_fixed = f"{base_redis_url}?ssl_cert_reqs=none&decode_responses=true"
            logger.info(f"📋 Fixed URL: {redis_url_fixed[:50]}...{redis_url_fixed[-20:]}")
            
            redis_client = redis.from_url(redis_url_fixed)
            
            # Test connection
            redis_client.ping()
            logger.info("✅ SUCCESS: Valkey URL query parameter connection established!")
            
            # Test operations to confirm full functionality
            test_key = "ai-hub:valkey:connection-test"
            redis_client.set(test_key, "valkey-url-params-working", ex=60)
            test_result = redis_client.get(test_key)
            logger.info(f"✅ Valkey operation test: {test_result}")
    
            return redis_client
            
        except Exception as e:
            logger.error(f"❌ Strategy 1 FAILED: {type(e).__name__}: {e}")
            redis_client = None
        
        # Strategy 2: Alternative URL parameter format (FIXED SSL PARAMETER)
        try:
            logger.info("🔄 Strategy 2: Alternative URL parameter format...")
            redis_url_alt = f"{base_redis_url}?ssl_cert_reqs=none&decode_responses=true"
            logger.info(f"📋 Alt URL: {redis_url_alt[:50]}...{redis_url_alt[-20:]}")
            
            redis_client = redis.from_url(redis_url_alt)
            redis_client.ping()
            logger.info("✅ SUCCESS: Alternative URL format connection established!")
            return redis_client
            
        except Exception as e:
            logger.error(f"❌ Strategy 2 FAILED: {type(e).__name__}: {e}")
            redis_client = None
        
        # Strategy 3: Simplified Valkey connection (no extra params)
        try:
            logger.info("🔧 Strategy 3: Simplified Valkey connection...")
            redis_client = redis.from_url(base_redis_url)
            redis_client.ping()
            logger.info("✅ SUCCESS: Simplified Valkey connection established!")
            return redis_client
            
        except Exception as e:
            logger.error(f"❌ Strategy 3 FAILED: {type(e).__name__}: {e}")
            redis_client = None
        
        # Strategy 4: Manual Redis constructor with parsed URL
        try:
            logger.info("🛠️ Strategy 4: Manual Redis constructor...")
            parsed = urlparse(base_redis_url)
            
            redis_client = redis.Redis(
                host=parsed.hostname,
                port=parsed.port,
                password=parsed.password,
                username=parsed.username or 'default',
                ssl=True if parsed.scheme == 'rediss' else False,
                ssl_cert_reqs=None,
                ssl_check_hostname=False,
                decode_responses=True,
                socket_timeout=10,
                socket_connect_timeout=15
            )
            
            redis_client.ping()
            logger.info("✅ SUCCESS: Manual constructor connection established!")
            return redis_client
            
        except Exception as e:
            logger.error(f"❌ Strategy 4 FAILED: {type(e).__name__}: {e}")
            redis_client = None
        
        # Strategy 5: Non-SSL fallback (last resort)
        try:
            logger.info("🔓 Strategy 5: Non-SSL fallback...")
            non_ssl_url = base_redis_url.replace('rediss://', 'redis://')
            logger.info(f"📋 Non-SSL URL: {non_ssl_url[:20]}...{non_ssl_url[-10:]}")
        
            redis_client = redis.from_url(non_ssl_url, decode_responses=True)
            redis_client.ping()
            logger.info("✅ SUCCESS: Non-SSL fallback connection established!")
            return redis_client
            
        except Exception as e:
            logger.error(f"❌ Strategy 5 FAILED: {type(e).__name__}: {e}")
            redis_client = None
        
        # All strategies failed
        logger.error("🚨 ALL VALKEY CONNECTION STRATEGIES FAILED!")
        logger.error("📋 Environment Variables Diagnostic:")
        logger.error(f"   REDIS_URL: {'SET (' + str(len(REDIS_URL)) + ' chars)' if REDIS_URL else 'MISSING'}")
        logger.error(f"   PORT: {os.getenv('PORT', 'MISSING')}")
        logger.error(f"   ENVIRONMENT: {os.getenv('ENVIRONMENT', 'MISSING')}")
        
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

# Frontend HTML with fixed web component guards
async def serve_frontend(request):
    """Serve the main frontend interface with proper web component guards"""
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>InstaBids AI Hub - MCP Interface</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1E40AF, #F59E0B);
            min-height: 100vh;
            color: white;
        }
        .container { 
            max-width: 1200px; 
            margin: 0 auto; 
            padding: 20px; 
        }
        .header {
            text-align: center;
            margin-bottom: 40px;
            padding: 30px 0;
        }
        .logo { 
            font-size: 3rem; 
            font-weight: 800; 
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .subtitle { 
            font-size: 1.2rem; 
            opacity: 0.9; 
        }
        .status-card {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 30px;
            border: 1px solid rgba(255,255,255,0.2);
        }
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .status-healthy { background: #10B981; }
        .status-error { background: #EF4444; }
        .mcp-tools {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }
        .tool-card {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid rgba(255,255,255,0.2);
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .tool-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.2);
        }
        .tool-name { 
            font-weight: 600; 
            margin-bottom: 8px; 
            color: #FCD34D;
        }
        .tool-desc { 
            font-size: 0.9rem; 
            opacity: 0.8; 
        }
        .btn {
            background: rgba(255,255,255,0.2);
            border: 1px solid rgba(255,255,255,0.3);
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.2s;
            margin: 5px;
        }
        .btn:hover {
            background: rgba(255,255,255,0.3);
            transform: translateY(-1px);
        }
        .endpoint-info {
            background: rgba(0,0,0,0.2);
            padding: 15px;
            border-radius: 8px;
            margin-top: 20px;
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 0.9rem;
        }
        .loading {
            opacity: 0.6;
            pointer-events: none;
        }
        .mcp-autosize-textarea {
            width: 100%;
            min-height: 100px;
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.3);
            border-radius: 8px;
            padding: 12px;
            color: white;
            font-family: inherit;
            resize: vertical;
        }
        .mcp-autosize-textarea::placeholder {
            color: rgba(255,255,255,0.6);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 class="logo">🚀 InstaBids AI Hub</h1>
            <p class="subtitle">Model Context Protocol Interface</p>
        </div>

        <div class="status-card">
            <h2>🔍 System Status</h2>
            <div id="system-status">
                <div>📡 <span class="status-indicator status-healthy"></span> Loading system status...</div>
            </div>
        </div>

        <div class="status-card">
            <h2>🛠️ Available MCP Tools</h2>
            <div id="mcp-tools-list">Loading tools...</div>
            
            <div class="endpoint-info">
                <strong>API Endpoints:</strong><br>
                • GET /mcp/tools - List available tools<br>
                • POST /mcp/call - Execute tool calls<br>
                • GET /health - System health check
            </div>
        </div>

        <div class="status-card">
            <h2>🧪 Tool Testing Interface</h2>
            <div>
                <select id="tool-selector" class="btn" style="width: 200px;">
                    <option value="">Select a tool...</option>
                </select>
                <button onclick="testTool()" class="btn">🚀 Test Tool</button>
            </div>
            
            <div style="margin-top: 15px;">
                <textarea id="tool-args" class="mcp-autosize-textarea" placeholder='{"arg1": "value1", "arg2": "value2"}'></textarea>
            </div>
            
            <div id="tool-result" style="margin-top: 15px; padding: 15px; background: rgba(0,0,0,0.2); border-radius: 8px; display: none;">
                <strong>Result:</strong>
                <pre id="result-content"></pre>
            </div>
        </div>
    </div>

    <script>
        // 🔧 WEB COMPONENT GUARDS - Prevent redefinition conflicts
        class McpAutosizeTextarea extends HTMLElement {
            constructor() {
                super();
                this.addEventListener('input', this.autoResize.bind(this));
            }
            
            autoResize() {
                this.style.height = 'auto';
                this.style.height = this.scrollHeight + 'px';
            }
            
            connectedCallback() {
                this.autoResize();
            }
        }

        // ✅ SAFE COMPONENT REGISTRATION - Only define if not already defined
        if (!customElements.get('mcp-autosize-textarea')) {
            customElements.define('mcp-autosize-textarea', McpAutosizeTextarea);
            console.log('✅ MCP autosize textarea component registered safely');
        } else {
            console.log('ℹ️ MCP autosize textarea component already exists - skipping redefinition');
        }

        // Initialize the interface
        let systemStatus = null;
        let availableTools = [];

        async function loadSystemStatus() {
            try {
                const response = await fetch('/health');
                systemStatus = await response.json();
                
                const statusEl = document.getElementById('system-status');
                const redisStatus = systemStatus.redis?.status || 'unknown';
                const statusClass = redisStatus === 'connected' ? 'status-healthy' : 'status-error';
                
                statusEl.innerHTML = `
                    <div>📡 <span class="status-indicator ${statusClass}"></span> Server: ${systemStatus.status}</div>
                    <div>🗄️ <span class="status-indicator ${statusClass}"></span> Redis: ${redisStatus}</div>
                    <div>⚡ <span class="status-indicator status-healthy"></span> Version: ${systemStatus.version}</div>
                    <div>🌐 <span class="status-indicator status-healthy"></span> Port: ${systemStatus.port}</div>
                `;
            } catch (error) {
                console.error('Failed to load system status:', error);
                document.getElementById('system-status').innerHTML = 
                    '<div>❌ <span class="status-indicator status-error"></span> Failed to load status</div>';
            }
        }

        async function loadMcpTools() {
            try {
                const response = await fetch('/mcp/tools');
                const data = await response.json();
                availableTools = data.tools || [];
                
                const toolsEl = document.getElementById('mcp-tools-list');
                const selectorEl = document.getElementById('tool-selector');
                
                if (availableTools.length === 0) {
                    toolsEl.innerHTML = '<p>No tools available</p>';
                    return;
                }
                
                // Populate tools display
                toolsEl.innerHTML = '<div class="mcp-tools">' + 
                    availableTools.map(tool => `
                        <div class="tool-card">
                            <div class="tool-name">${tool.name}</div>
                            <div class="tool-desc">${tool.description}</div>
                        </div>
                    `).join('') + '</div>';
                
                // Populate tool selector
                selectorEl.innerHTML = '<option value="">Select a tool...</option>' +
                    availableTools.map(tool => `<option value="${tool.name}">${tool.name}</option>`).join('');
                
            } catch (error) {
                console.error('Failed to load MCP tools:', error);
                document.getElementById('mcp-tools-list').innerHTML = '<p>❌ Failed to load tools</p>';
            }
        }

        async function testTool() {
            const toolName = document.getElementById('tool-selector').value;
            const argsText = document.getElementById('tool-args').value;
            const resultEl = document.getElementById('tool-result');
            const contentEl = document.getElementById('result-content');
            
            if (!toolName) {
                alert('Please select a tool first');
                return;
            }
            
            let args = {};
            if (argsText.trim()) {
                try {
                    args = JSON.parse(argsText);
                } catch (error) {
                    alert('Invalid JSON in arguments field');
                    return;
                }
            }
            
            try {
                resultEl.style.display = 'block';
                contentEl.textContent = 'Loading...';
                
                const response = await fetch('/mcp/call', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: toolName, arguments: args })
                });
                
                const result = await response.json();
                contentEl.textContent = JSON.stringify(result, null, 2);
                
            } catch (error) {
                contentEl.textContent = 'Error: ' + error.message;
            }
        }

        // Initialize on page load
        document.addEventListener('DOMContentLoaded', () => {
            loadSystemStatus();
            loadMcpTools();
            
            // Refresh status every 30 seconds
            setInterval(loadSystemStatus, 30000);
        });
    </script>
</body>
</html>"""
    
    return web.Response(text=html_content, content_type='text/html')

# HTTP Handlers
async def health_check(request):
    """Enhanced health check endpoint with Valkey diagnostics"""
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
            
            logger.info(f"✅ Health check passed - Valkey connected: {redis_details}")
            
        except Exception as e:
            redis_status = f"error: {str(e)}"
            redis_details = {"error": str(e)}
            logger.error(f"❌ Health check Valkey error: {e}")
    else:
        logger.warning("⚠️ Health check - Valkey client not available")
    
    return web.json_response({
        "status": "healthy",
        "service": "InstaBids AI Hub",
        "version": "2.2.0-valkey-fixed",
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
        
        logger.info(f"🛠️ MCP Tool called: {tool_name} with args: {args}")
        
        # Log tool usage to Valkey
        redis = get_redis_client()
        if redis:
            try:
                redis.hincrby("ai-hub:tool_usage", tool_name, 1)
                logger.debug(f"📋 Tool usage logged for: {tool_name}")
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
    """Run the Valkey-fixed HTTP MCP server"""
    app = web.Application()
    
    # Routes
    app.router.add_get('/', serve_frontend)  # 🎉 NEW: Frontend interface
    app.router.add_get('/health', health_check)
    app.router.add_get('/mcp/tools', mcp_tools)
    app.router.add_post('/mcp/call', mcp_call_tool)
    
    # Initialize Valkey connection with URL query parameter approach
    logger.info("🚀 Starting InstaBids AI Hub VALKEY-FIXED Server...")
    redis = get_redis_client()
    if redis:
        try:
            redis.set("ai-hub:mcp_server:status", "running")
            redis.set("ai-hub:mcp_server:start_time", datetime.now().isoformat())
            redis.set("ai-hub:mcp_server:version", "2.2.0-valkey-fixed")
            logger.info("🔗 Valkey integration enabled successfully")
        except Exception as e:
            logger.error(f"❌ Valkey init failed: {e}")
    else:
        logger.warning("📱 Running without Valkey (non-critical)")
    
    logger.info(f"🌐 Starting InstaBids AI Hub on port {PORT}")
    logger.info(f"✅ Health Check: http://localhost:{PORT}/health")
    logger.info(f"🛠️ MCP Tools: http://localhost:{PORT}/mcp/tools")
    logger.info(f"⚡ MCP Call: http://localhost:{PORT}/mcp/call")
    logger.info(f"🎨 Frontend UI: http://localhost:{PORT}/")  # 🎉 NEW: Frontend endpoint
    
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
