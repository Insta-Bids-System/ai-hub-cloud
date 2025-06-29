#!/usr/bin/env python3
"""
Open WebUI MCP Server - Persistent Implementation
Tools for AI self-modification with full persistence
"""

from fastapi import FastAPI, Request, HTTPException
from typing import Dict, Any, List, Optional
import json
import httpx
import os
import aiofiles
from pathlib import Path
from datetime import datetime

app = FastAPI(title="InstaBids AI Hub MCP Server")

# Configuration
OPENWEBUI_BASE_URL = os.getenv("OPENWEBUI_URL", "http://open-webui:8080")
WORKSPACE_PATH = Path(os.getenv("WORKSPACE_PATH", "/app/workspace"))
MCP_PORT = int(os.getenv("MCP_PORT", "8888"))
MCP_HOST = os.getenv("MCP_HOST", "0.0.0.0")

# Ensure workspace exists
WORKSPACE_PATH.mkdir(parents=True, exist_ok=True)

# Tools registry
tools_registry = {}

def mcp_tool(func):
    """Decorator to register MCP tools"""
    tools_registry[func.__name__] = {
        "name": func.__name__,
        "description": func.__doc__ or "",
        "function": func,
        "parameters": func.__annotations__
    }
    return func

async def call_openwebui_api(method: str, endpoint: str, data: Dict = None):
    """Helper function to call Open WebUI APIs"""
    url = f"{OPENWEBUI_BASE_URL}{endpoint}"
    api_key = os.getenv("OPENWEBUI_API_KEY")
    
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    async with httpx.AsyncClient() as client:
        if method.upper() == "GET":
            response = await client.get(url, params=data or {}, headers=headers)
        elif method.upper() == "POST":
            response = await client.post(url, json=data or {}, headers=headers)
        elif method.upper() == "PUT":
            response = await client.put(url, json=data or {}, headers=headers)
        elif method.upper() == "DELETE":
            response = await client.delete(url, json=data or {}, headers=headers)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported method: {method}")
    
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    
    return response.json()

# FILE SYSTEM TOOLS
@mcp_tool
async def create_project(name: str, description: str = "") -> dict:
    """Create a new project directory with metadata tracking"""
    project_path = WORKSPACE_PATH / name
    project_path.mkdir(parents=True, exist_ok=True)
    
    metadata = {
        "name": name,
        "description": description,
        "created": datetime.now().isoformat(),
        "files": [],
        "ai_managed": True
    }
    
    metadata_path = project_path / ".project.json"
    async with aiofiles.open(metadata_path, 'w') as f:
        await f.write(json.dumps(metadata, indent=2))
    
    return {
        "status": "success",
        "path": str(project_path),
        "message": f"Project '{name}' created at {project_path}"
    }

@mcp_tool
async def write_code(project: str, filename: str, content: str, language: str = "python") -> dict:
    """Write code to workspace with version tracking"""
    file_path = WORKSPACE_PATH / project / filename
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    async with aiofiles.open(file_path, 'w') as f:
        await f.write(content)
    
    # Update project metadata
    metadata_path = WORKSPACE_PATH / project / ".project.json"
    if metadata_path.exists():
        async with aiofiles.open(metadata_path, 'r') as f:
            metadata = json.loads(await f.read())
        
        file_info = {
            "name": filename,
            "language": language,
            "size": len(content),
            "updated": datetime.now().isoformat()
        }
        
        # Update or add file info
        metadata["files"] = [f for f in metadata.get("files", []) if f["name"] != filename]
        metadata["files"].append(file_info)
        
        async with aiofiles.open(metadata_path, 'w') as f:
            await f.write(json.dumps(metadata, indent=2))
    
    return {
        "status": "success",
        "path": str(file_path),
        "message": f"Code written to {file_path}"
    }

@mcp_tool
async def read_code(project: str, filename: str) -> dict:
    """Read code from workspace"""
    file_path = WORKSPACE_PATH / project / filename
    
    if not file_path.exists():
        return {
            "status": "error",
            "message": f"File not found: {file_path}"
        }
    
    async with aiofiles.open(file_path, 'r') as f:
        content = await f.read()
    
    return {
        "status": "success",
        "content": content,
        "path": str(file_path)
    }

@mcp_tool
async def list_projects() -> dict:
    """List all projects in the workspace"""
    projects = []
    
    for path in WORKSPACE_PATH.iterdir():
        if path.is_dir() and not path.name.startswith('.'):
            metadata_path = path / ".project.json"
            if metadata_path.exists():
                async with aiofiles.open(metadata_path, 'r') as f:
                    metadata = json.loads(await f.read())
                projects.append(metadata)
            else:
                projects.append({
                    "name": path.name,
                    "description": "No metadata",
                    "created": "Unknown"
                })
    
    return {
        "status": "success",
        "projects": projects,
        "count": len(projects)
    }

# OPEN WEBUI API TOOLS
@mcp_tool
async def get_health():
    """Check Open WebUI health status"""
    return await call_openwebui_api("GET", "/health")

@mcp_tool
async def list_models():
    """List all available models"""
    return await call_openwebui_api("GET", "/api/models")

@mcp_tool
async def create_chat(title: str = "New Chat"):
    """Create new chat"""
    return await call_openwebui_api("POST", "/api/v1/chats/new", {"title": title})

@mcp_tool
async def list_chats():
    """Get all chats for current user"""
    return await call_openwebui_api("GET", "/api/v1/chats/")

@mcp_tool
async def create_function(name: str, code: str, description: str = ""):
    """Create new function for AI self-modification"""
    return await call_openwebui_api("POST", "/api/v1/functions/create", {
        "name": name,
        "code": code,
        "description": description
    })

@mcp_tool
async def list_functions():
    """List all functions"""
    return await call_openwebui_api("GET", "/api/v1/functions/")

# MCP SERVER ENDPOINTS
@app.post("/mcp/call")
async def mcp_call(request: Request):
    """Main MCP tool calling endpoint"""
    try:
        data = await request.json()
        tool_name = data.get("tool")
        parameters = data.get("parameters", {})
        
        if tool_name not in tools_registry:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
        
        tool = tools_registry[tool_name]
        result = await tool["function"](**parameters)
        
        return {
            "status": "success",
            "tool": tool_name,
            "result": result
        }
    except Exception as e:
        return {
            "status": "error",
            "tool": tool_name,
            "error": str(e)
        }

@app.get("/mcp/tools")
async def list_tools():
    """List all available MCP tools"""
    tools_list = []
    for name, tool in tools_registry.items():
        tools_list.append({
            "name": name,
            "description": tool["description"],
            "parameters": list(tool.get("parameters", {}).keys())
        })
    
    return {
        "tools": tools_list,
        "total": len(tools_list)
    }

@app.get("/")
async def root():
    """Root endpoint - server info"""
    return {
        "name": "InstaBids AI Hub MCP Server",
        "version": "1.0",
        "status": "operational",
        "tools_count": len(tools_registry),
        "workspace": str(WORKSPACE_PATH),
        "endpoints": {
            "tools_list": "/mcp/tools",
            "tool_call": "/mcp/call",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "tools_loaded": len(tools_registry)
    }

# SSE endpoint for Claude Desktop
@app.get("/sse")
async def sse_endpoint(request: Request):
    """Server-Sent Events endpoint for MCP tools"""
    from starlette.responses import StreamingResponse
    import asyncio
    
    async def event_generator():
        # Send initial tools list
        tools_data = {
            "type": "tools",
            "tools": [
                {
                    "name": tool_name,
                    "description": tool_info["description"],
                    "parameters": list(tool_info.get("parameters", {}).keys())
                }
                for tool_name, tool_info in tools_registry.items()
            ]
        }
        yield f"data: {json.dumps(tools_data)}\n\n"
        
        # Keep connection alive
        while True:
            await asyncio.sleep(30)
            yield f"data: {json.dumps({'type': 'ping'})}\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    
    print(f"🚀 Starting InstaBids AI Hub MCP Server")
    print(f"📁 Workspace: {WORKSPACE_PATH}")
    print(f"🔧 Tools loaded: {len(tools_registry)}")
    print(f"🌐 Open WebUI URL: {OPENWEBUI_BASE_URL}")
    
    uvicorn.run(app, host=MCP_HOST, port=MCP_PORT)
