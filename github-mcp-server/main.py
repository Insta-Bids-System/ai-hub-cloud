#!/usr/bin/env python3
"""
GitHub MCP Server - Claude's Exact GitHub Tools
Gives AI agents the same GitHub capabilities Claude has
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, List, Optional
import json
import httpx
import os
import base64
from datetime import datetime
import asyncio

# =============================================================================
# GITHUB MCP SERVER - CLAUDE'S EXACT TOOLS
# =============================================================================

app = FastAPI(title="GitHub MCP Server - Claude's Tools")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
MCP_PORT = int(os.getenv("MCP_PORT", "3001"))
MCP_HOST = os.getenv("MCP_HOST", "0.0.0.0")

# Tools registry
tools_registry = {}

# GitHub API base URL
GITHUB_API = "https://api.github.com"

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

async def github_api_call(method: str, endpoint: str, data: Dict = None, params: Dict = None):
    """Make authenticated GitHub API calls"""
    url = f"{GITHUB_API}{endpoint}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "InstaBids-AI-Hub"
    }
    
    async with httpx.AsyncClient() as client:
        if method.upper() == "GET":
            response = await client.get(url, headers=headers, params=params or {})
        elif method.upper() == "POST":
            response = await client.post(url, headers=headers, json=data or {})
        elif method.upper() == "PUT":
            response = await client.put(url, headers=headers, json=data or {})
        elif method.upper() == "DELETE":
            response = await client.delete(url, headers=headers)
        elif method.upper() == "PATCH":
            response = await client.patch(url, headers=headers, json=data or {})
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported method: {method}")
    
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    
    return response.json()

def mcp_tool(func):
    """Decorator to register MCP tools"""
    tools_registry[func.__name__] = {
        "name": func.__name__,
        "description": func.__doc__ or "",
        "function": func,
        "parameters": func.__annotations__
    }
    return func

# =============================================================================
# CLAUDE'S EXACT GITHUB TOOLS
# =============================================================================

@mcp_tool
async def create_repository(name: str, description: str = "", private: bool = False, auto_init: bool = True):
    """Create a new GitHub repository"""
    data = {
        "name": name,
        "description": description,
        "private": private,
        "auto_init": auto_init
    }
    return await github_api_call("POST", "/user/repos", data)

@mcp_tool
async def get_repository(owner: str, repo: str):
    """Get repository information"""
    return await github_api_call("GET", f"/repos/{owner}/{repo}")

@mcp_tool
async def list_repositories(per_page: int = 30, page: int = 1):
    """List user's repositories"""
    params = {"per_page": per_page, "page": page, "sort": "updated"}
    return await github_api_call("GET", "/user/repos", params=params)

@mcp_tool
async def create_or_update_file(owner: str, repo: str, path: str, content: str, message: str, branch: str = "main", sha: str = None):
    """Create or update a file in repository"""
    # Encode content to base64
    encoded_content = base64.b64encode(content.encode()).decode()
    
    data = {
        "message": message,
        "content": encoded_content,
        "branch": branch
    }
    
    if sha:
        data["sha"] = sha
    
    return await github_api_call("PUT", f"/repos/{owner}/{repo}/contents/{path}", data)

@mcp_tool
async def get_file_contents(owner: str, repo: str, path: str, branch: str = None):
    """Get file contents from repository"""
    params = {"ref": branch} if branch else {}
    response = await github_api_call("GET", f"/repos/{owner}/{repo}/contents/{path}", params=params)
    
    # Decode base64 content
    if "content" in response:
        response["decoded_content"] = base64.b64decode(response["content"]).decode()
    
    return response

@mcp_tool
async def delete_file(owner: str, repo: str, path: str, message: str, sha: str, branch: str = "main"):
    """Delete a file from repository"""
    data = {
        "message": message,
        "sha": sha,
        "branch": branch
    }
    return await github_api_call("DELETE", f"/repos/{owner}/{repo}/contents/{path}", data)

@mcp_tool
async def list_branches(owner: str, repo: str, per_page: int = 30, page: int = 1):
    """List repository branches"""
    params = {"per_page": per_page, "page": page}
    return await github_api_call("GET", f"/repos/{owner}/{repo}/branches", params=params)

@mcp_tool
async def create_branch(owner: str, repo: str, branch: str, from_branch: str = "main"):
    """Create a new branch"""
    # Get the SHA of the source branch
    ref_data = await github_api_call("GET", f"/repos/{owner}/{repo}/git/refs/heads/{from_branch}")
    sha = ref_data["object"]["sha"]
    
    # Create new branch
    data = {
        "ref": f"refs/heads/{branch}",
        "sha": sha
    }
    return await github_api_call("POST", f"/repos/{owner}/{repo}/git/refs", data)

@mcp_tool
async def get_branch(owner: str, repo: str, branch: str):
    """Get branch information"""
    return await github_api_call("GET", f"/repos/{owner}/{repo}/branches/{branch}")

@mcp_tool
async def list_commits(owner: str, repo: str, sha: str = None, per_page: int = 30, page: int = 1):
    """List repository commits"""
    params = {"per_page": per_page, "page": page}
    if sha:
        params["sha"] = sha
    return await github_api_call("GET", f"/repos/{owner}/{repo}/commits", params=params)

@mcp_tool
async def get_commit(owner: str, repo: str, sha: str):
    """Get specific commit details"""
    return await github_api_call("GET", f"/repos/{owner}/{repo}/commits/{sha}")

@mcp_tool
async def create_pull_request(owner: str, repo: str, title: str, head: str, base: str, body: str = "", draft: bool = False):
    """Create a new pull request"""
    data = {
        "title": title,
        "head": head,
        "base": base,
        "body": body,
        "draft": draft
    }
    return await github_api_call("POST", f"/repos/{owner}/{repo}/pulls", data)

@mcp_tool
async def list_pull_requests(owner: str, repo: str, state: str = "open", per_page: int = 30, page: int = 1):
    """List repository pull requests"""
    params = {"state": state, "per_page": per_page, "page": page}
    return await github_api_call("GET", f"/repos/{owner}/{repo}/pulls", params=params)

@mcp_tool
async def get_pull_request(owner: str, repo: str, pull_number: int):
    """Get specific pull request"""
    return await github_api_call("GET", f"/repos/{owner}/{repo}/pulls/{pull_number}")

@mcp_tool
async def merge_pull_request(owner: str, repo: str, pull_number: int, commit_title: str = None, commit_message: str = None, merge_method: str = "merge"):
    """Merge a pull request"""
    data = {"merge_method": merge_method}
    if commit_title:
        data["commit_title"] = commit_title
    if commit_message:
        data["commit_message"] = commit_message
    
    return await github_api_call("PUT", f"/repos/{owner}/{repo}/pulls/{pull_number}/merge", data)

@mcp_tool
async def create_issue(owner: str, repo: str, title: str, body: str = "", labels: List[str] = None, assignees: List[str] = None):
    """Create a new issue"""
    data = {
        "title": title,
        "body": body
    }
    if labels:
        data["labels"] = labels
    if assignees:
        data["assignees"] = assignees
    
    return await github_api_call("POST", f"/repos/{owner}/{repo}/issues", data)

@mcp_tool
async def list_issues(owner: str, repo: str, state: str = "open", per_page: int = 30, page: int = 1):
    """List repository issues"""
    params = {"state": state, "per_page": per_page, "page": page}
    return await github_api_call("GET", f"/repos/{owner}/{repo}/issues", params=params)

@mcp_tool
async def get_issue(owner: str, repo: str, issue_number: int):
    """Get specific issue"""
    return await github_api_call("GET", f"/repos/{owner}/{repo}/issues/{issue_number}")

@mcp_tool
async def update_issue(owner: str, repo: str, issue_number: int, title: str = None, body: str = None, state: str = None, labels: List[str] = None):
    """Update an issue"""
    data = {}
    if title:
        data["title"] = title
    if body:
        data["body"] = body
    if state:
        data["state"] = state
    if labels:
        data["labels"] = labels
    
    return await github_api_call("PATCH", f"/repos/{owner}/{repo}/issues/{issue_number}", data)

@mcp_tool
async def add_issue_comment(owner: str, repo: str, issue_number: int, body: str):
    """Add comment to issue"""
    data = {"body": body}
    return await github_api_call("POST", f"/repos/{owner}/{repo}/issues/{issue_number}/comments", data)

@mcp_tool
async def list_repository_contents(owner: str, repo: str, path: str = "", branch: str = None):
    """List repository contents"""
    params = {"ref": branch} if branch else {}
    return await github_api_call("GET", f"/repos/{owner}/{repo}/contents/{path}", params=params)

@mcp_tool
async def create_release(owner: str, repo: str, tag_name: str, name: str, body: str = "", draft: bool = False, prerelease: bool = False):
    """Create a new release"""
    data = {
        "tag_name": tag_name,
        "name": name,
        "body": body,
        "draft": draft,
        "prerelease": prerelease
    }
    return await github_api_call("POST", f"/repos/{owner}/{repo}/releases", data)

@mcp_tool
async def list_releases(owner: str, repo: str, per_page: int = 30, page: int = 1):
    """List repository releases"""
    params = {"per_page": per_page, "page": page}
    return await github_api_call("GET", f"/repos/{owner}/{repo}/releases", params=params)

@mcp_tool
async def get_user():
    """Get authenticated user information"""
    return await github_api_call("GET", "/user")

@mcp_tool
async def search_repositories(query: str, sort: str = "updated", order: str = "desc", per_page: int = 30, page: int = 1):
    """Search repositories"""
    params = {
        "q": query,
        "sort": sort,
        "order": order,
        "per_page": per_page,
        "page": page
    }
    return await github_api_call("GET", "/search/repositories", params=params)

@mcp_tool
async def fork_repository(owner: str, repo: str, organization: str = None):
    """Fork a repository"""
    data = {}
    if organization:
        data["organization"] = organization
    
    return await github_api_call("POST", f"/repos/{owner}/{repo}/forks", data)

@mcp_tool
async def star_repository(owner: str, repo: str):
    """Star a repository"""
    return await github_api_call("PUT", f"/user/starred/{owner}/{repo}")

@mcp_tool
async def unstar_repository(owner: str, repo: str):
    """Unstar a repository"""
    return await github_api_call("DELETE", f"/user/starred/{owner}/{repo}")

@mcp_tool
async def list_starred_repositories(per_page: int = 30, page: int = 1):
    """List starred repositories"""
    params = {"per_page": per_page, "page": page}
    return await github_api_call("GET", "/user/starred", params=params)

@mcp_tool
async def get_repository_languages(owner: str, repo: str):
    """Get repository programming languages"""
    return await github_api_call("GET", f"/repos/{owner}/{repo}/languages")

@mcp_tool
async def get_repository_topics(owner: str, repo: str):
    """Get repository topics"""
    return await github_api_call("GET", f"/repos/{owner}/{repo}/topics")

@mcp_tool
async def replace_repository_topics(owner: str, repo: str, topics: List[str]):
    """Replace repository topics"""
    data = {"names": topics}
    return await github_api_call("PUT", f"/repos/{owner}/{repo}/topics", data)

# =============================================================================
# ADVANCED GITHUB TOOLS
# =============================================================================

@mcp_tool
async def push_multiple_files(owner: str, repo: str, files: List[Dict], message: str, branch: str = "main"):
    """Push multiple files in a single commit using GitHub's Tree API"""
    try:
        # Get the latest commit SHA
        ref = await github_api_call("GET", f"/repos/{owner}/{repo}/git/refs/heads/{branch}")
        latest_commit_sha = ref["object"]["sha"]
        
        # Get the tree SHA from the latest commit
        commit = await github_api_call("GET", f"/repos/{owner}/{repo}/git/commits/{latest_commit_sha}")
        base_tree_sha = commit["tree"]["sha"]
        
        # Create tree objects for all files
        tree_items = []
        for file_info in files:
            # Create blob for file content
            blob_data = {
                "content": file_info["content"],
                "encoding": "utf-8"
            }
            blob = await github_api_call("POST", f"/repos/{owner}/{repo}/git/blobs", blob_data)
            
            # Add to tree
            tree_items.append({
                "path": file_info["path"],
                "mode": "100644",
                "type": "blob",
                "sha": blob["sha"]
            })
        
        # Create new tree
        tree_data = {
            "base_tree": base_tree_sha,
            "tree": tree_items
        }
        tree = await github_api_call("POST", f"/repos/{owner}/{repo}/git/trees", tree_data)
        
        # Create new commit
        commit_data = {
            "message": message,
            "tree": tree["sha"],
            "parents": [latest_commit_sha]
        }
        new_commit = await github_api_call("POST", f"/repos/{owner}/{repo}/git/commits", commit_data)
        
        # Update branch reference
        ref_data = {
            "sha": new_commit["sha"]
        }
        await github_api_call("PATCH", f"/repos/{owner}/{repo}/git/refs/heads/{branch}", ref_data)
        
        return {
            "success": True,
            "commit_sha": new_commit["sha"],
            "files_pushed": len(files),
            "message": f"Successfully pushed {len(files)} files"
        }
    except Exception as e:
        return {"error": f"Failed to push files: {str(e)}"}

# =============================================================================
# MCP SERVER ENDPOINTS
# =============================================================================

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
            "tool": tool_name if 'tool_name' in locals() else "unknown",
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
        "name": "GitHub MCP Server",
        "description": "Claude's exact GitHub tools for AI agents",
        "version": "1.0",
        "status": "operational",
        "tools_count": len(tools_registry),
        "capabilities": [
            "Repository management",
            "File operations", 
            "Branch management",
            "Pull requests",
            "Issues",
            "Releases",
            "User operations"
        ],
        "endpoints": {
            "tools_list": "/mcp/tools",
            "tool_call": "/mcp/call", 
            "health": "/health",
            "sse": "/sse"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test GitHub API connection
        user = await get_user()
        return {
            "status": "healthy",
            "github_api": "connected",
            "authenticated_user": user.get("login", "unknown"),
            "tools_loaded": len(tools_registry),
            "timestamp": datetime.now().isoformat()
        }
    except:
        return {
            "status": "healthy",
            "github_api": "disconnected",
            "tools_loaded": len(tools_registry),
            "timestamp": datetime.now().isoformat()
        }

# SSE endpoint for MCP integration
@app.get("/sse")
async def sse_endpoint():
    """Server-Sent Events endpoint for MCP integration"""
    async def event_generator():
        # Send connection message
        yield f"data: {json.dumps({'type': 'connection', 'status': 'connected'})}\n\n"
        
        # Send all tools
        tools_data = []
        for tool_name, tool_info in tools_registry.items():
            tools_data.append({
                "name": tool_name,
                "description": tool_info["description"]
            })
        
        yield f"data: {json.dumps({'type': 'tools', 'tools': tools_data})}\n\n"
        
        # Keep alive
        while True:
            await asyncio.sleep(30)
            yield f"data: {json.dumps({'type': 'ping'})}\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")

# =============================================================================
# SERVER STARTUP
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print(f"🐙 Starting GitHub MCP Server - Claude's Tools")
    print(f"📍 Host: {MCP_HOST}")
    print(f"🔌 Port: {MCP_PORT}")
    print(f"🔧 GitHub Tools: {len(tools_registry)}")
    print(f"🔑 GitHub Token: {'✅ Set' if GITHUB_TOKEN else '❌ Missing'}")
    print(f"✅ Server ready!")
    
    uvicorn.run(app, host=MCP_HOST, port=MCP_PORT)
