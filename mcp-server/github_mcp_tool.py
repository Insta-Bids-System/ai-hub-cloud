#!/usr/bin/env python3
"""
GitHub MCP Tool - Exact same capabilities that Claude used to deploy FileBrowser
Created for InstaBids AI Hub - Revolutionary Self-Modifying AI System
"""

import os
import httpx
import base64
from typing import Dict, Any, List, Optional

# GitHub API configuration
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_API_BASE = "https://api.github.com"

class GitHubMCPTool:
    """GitHub MCP Tool with all capabilities used in FileBrowser deployment"""
    
    def __init__(self, token: str = None):
        self.token = token or GITHUB_TOKEN
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }
    
    async def get_file_contents(self, owner: str, repo: str, path: str, branch: str = "main") -> Dict[str, Any]:
        """Get file contents from GitHub repository - EXACT same as Claude used"""
        async with httpx.AsyncClient() as client:
            url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{path}"
            params = {"ref": branch}
            
            response = await client.get(url, headers=self.headers, params=params)
            
            if response.status_code == 404:
                return {"error": "File not found", "status_code": 404}
            
            response.raise_for_status()
            data = response.json()
            
            if data.get("type") == "file":
                # Decode base64 content
                content = base64.b64decode(data["content"]).decode('utf-8')
                return {
                    "content": content,
                    "sha": data["sha"],
                    "path": data["path"],
                    "size": data["size"]
                }
            
            return data
    
    async def create_or_update_file(self, owner: str, repo: str, path: str, content: str, 
                                   message: str, branch: str = "main", sha: str = None) -> Dict[str, Any]:
        """Create or update file - EXACT same as Claude used for Dockerfile creation"""
        async with httpx.AsyncClient() as client:
            url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{path}"
            
            # Encode content to base64
            encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
            
            payload = {
                "message": message,
                "content": encoded_content,
                "branch": branch
            }
            
            # Add SHA if updating existing file
            if sha:
                payload["sha"] = sha
            
            response = await client.put(url, headers=self.headers, json=payload)
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                return {"error": response.text, "status_code": response.status_code}
    
    async def list_branches(self, owner: str, repo: str) -> List[Dict[str, Any]]:
        """List repository branches - used for verification"""
        async with httpx.AsyncClient() as client:
            url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/branches"
            
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            
            return response.json()
    
    async def get_repository(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get repository information"""
        async with httpx.AsyncClient() as client:
            url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}"
            
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            
            return response.json()
    
    async def list_repository_contents(self, owner: str, repo: str, path: str = "") -> List[Dict[str, Any]]:
        """List repository contents at path"""
        async with httpx.AsyncClient() as client:
            url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{path}"
            
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            
            return response.json()
    
    async def create_repository(self, name: str, description: str = "", private: bool = False) -> Dict[str, Any]:
        """Create new repository"""
        async with httpx.AsyncClient() as client:
            url = f"{GITHUB_API_BASE}/user/repos"
            
            payload = {
                "name": name,
                "description": description,
                "private": private,
                "auto_init": True
            }
            
            response = await client.post(url, headers=self.headers, json=payload)
            
            if response.status_code == 201:
                return response.json()
            else:
                return {"error": response.text, "status_code": response.status_code}
    
    async def delete_file(self, owner: str, repo: str, path: str, message: str, 
                         sha: str, branch: str = "main") -> Dict[str, Any]:
        """Delete file from repository"""
        async with httpx.AsyncClient() as client:
            url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{path}"
            
            payload = {
                "message": message,
                "sha": sha,
                "branch": branch
            }
            
            response = await client.delete(url, headers=self.headers, json=payload)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": response.text, "status_code": response.status_code}

# Export for MCP server integration
github_tool = GitHubMCPTool()

# MCP Tool Functions - Ready for revolutionary_complete.py integration
async def github_get_file_contents(owner: str, repo: str, path: str, branch: str = "main"):
    """MCP Tool: Get file contents from GitHub repository"""
    return await github_tool.get_file_contents(owner, repo, path, branch)

async def github_create_or_update_file(owner: str, repo: str, path: str, content: str, 
                                      message: str, branch: str = "main", sha: str = None):
    """MCP Tool: Create or update file in GitHub repository"""
    return await github_tool.create_or_update_file(owner, repo, path, content, message, branch, sha)

async def github_list_branches(owner: str, repo: str):
    """MCP Tool: List repository branches"""
    return await github_tool.list_branches(owner, repo)

async def github_get_repository(owner: str, repo: str):
    """MCP Tool: Get repository information"""
    return await github_tool.get_repository(owner, repo)

async def github_list_contents(owner: str, repo: str, path: str = ""):
    """MCP Tool: List repository contents"""
    return await github_tool.list_repository_contents(owner, repo, path)

async def github_create_repository(name: str, description: str = "", private: bool = False):
    """MCP Tool: Create new repository"""
    return await github_tool.create_repository(name, description, private)

async def github_delete_file(owner: str, repo: str, path: str, message: str, sha: str, branch: str = "main"):
    """MCP Tool: Delete file from repository"""
    return await github_tool.delete_file(owner, repo, path, message, sha, branch)
