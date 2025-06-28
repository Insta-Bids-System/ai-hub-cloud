#!/usr/bin/env python3
"""
DigitalOcean MCP Tool - Exact same capabilities that Claude used to deploy FileBrowser
Created for InstaBids AI Hub - Revolutionary Self-Modifying AI System
"""

import os
import httpx
from typing import Dict, Any, List, Optional

# DigitalOcean API configuration
DO_TOKEN = os.getenv("DIGITALOCEAN_TOKEN", "")
DO_API_BASE = "https://api.digitalocean.com/v2"

class DigitalOceanMCPTool:
    """DigitalOcean MCP Tool with all capabilities used in FileBrowser deployment"""
    
    def __init__(self, token: str = None):
        self.token = token or DO_TOKEN
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    async def list_apps(self, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """List all apps - EXACT same as Claude used to find correct app ID"""
        async with httpx.AsyncClient() as client:
            url = f"{DO_API_BASE}/apps"
            params = {"page": page, "per_page": per_page}
            
            response = await client.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            return response.json()
    
    async def get_app(self, app_id: str) -> Dict[str, Any]:
        """Get app details - EXACT same as Claude used to inspect current config"""
        async with httpx.AsyncClient() as client:
            url = f"{DO_API_BASE}/apps/{app_id}"
            
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            
            return response.json()
    
    async def update_app(self, app_id: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Update app configuration - EXACT same as Claude used to add FileBrowser"""
        async with httpx.AsyncClient() as client:
            url = f"{DO_API_BASE}/apps/{app_id}"
            
            payload = {"spec": spec}
            
            response = await client.put(url, headers=self.headers, json=payload)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": response.text, "status_code": response.status_code}
    
    async def create_app(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Create new app"""
        async with httpx.AsyncClient() as client:
            url = f"{DO_API_BASE}/apps"
            
            payload = {"spec": spec}
            
            response = await client.post(url, headers=self.headers, json=payload)
            
            if response.status_code == 201:
                return response.json()
            else:
                return {"error": response.text, "status_code": response.status_code}
    
    async def delete_app(self, app_id: str) -> Dict[str, Any]:
        """Delete app"""
        async with httpx.AsyncClient() as client:
            url = f"{DO_API_BASE}/apps/{app_id}"
            
            response = await client.delete(url, headers=self.headers)
            
            if response.status_code == 204:
                return {"success": True, "message": "App deleted successfully"}
            else:
                return {"error": response.text, "status_code": response.status_code}
    
    async def create_deployment(self, app_id: str, force_build: bool = False) -> Dict[str, Any]:
        """Create deployment - EXACT same as Claude used to deploy FileBrowser"""
        async with httpx.AsyncClient() as client:
            url = f"{DO_API_BASE}/apps/{app_id}/deployments"
            
            payload = {"force_build": force_build}
            
            response = await client.post(url, headers=self.headers, json=payload)
            
            if response.status_code == 201:
                return response.json()
            else:
                return {"error": response.text, "status_code": response.status_code}
    
    async def get_deployment(self, app_id: str, deployment_id: str) -> Dict[str, Any]:
        """Get deployment status - EXACT same as Claude used to monitor progress"""
        async with httpx.AsyncClient() as client:
            url = f"{DO_API_BASE}/apps/{app_id}/deployments/{deployment_id}"
            
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            
            return response.json()
    
    async def list_deployments(self, app_id: str, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """List deployments for an app"""
        async with httpx.AsyncClient() as client:
            url = f"{DO_API_BASE}/apps/{app_id}/deployments"
            params = {"page": page, "per_page": per_page}
            
            response = await client.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            return response.json()
    
    async def get_deployment_logs(self, app_id: str, deployment_id: str, 
                                 component_name: str = None, log_type: str = "BUILD") -> str:
        """Get deployment logs"""
        async with httpx.AsyncClient() as client:
            url = f"{DO_API_BASE}/apps/{app_id}/deployments/{deployment_id}/logs"
            params = {"type": log_type}
            
            if component_name:
                params["component_name"] = component_name
            
            response = await client.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                # Return logs URL or redirect to actual logs
                return response.text
            else:
                return f"Error getting logs: {response.text}"
    
    async def cancel_deployment(self, app_id: str, deployment_id: str) -> Dict[str, Any]:
        """Cancel deployment"""
        async with httpx.AsyncClient() as client:
            url = f"{DO_API_BASE}/apps/{app_id}/deployments/{deployment_id}/cancel"
            
            response = await client.post(url, headers=self.headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": response.text, "status_code": response.status_code}
    
    async def list_regions(self) -> Dict[str, Any]:
        """List available regions"""
        async with httpx.AsyncClient() as client:
            url = f"{DO_API_BASE}/apps/regions"
            
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            
            return response.json()
    
    async def list_instance_sizes(self) -> Dict[str, Any]:
        """List available instance sizes"""
        async with httpx.AsyncClient() as client:
            url = f"{DO_API_BASE}/apps/tiers/instance_sizes"
            
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            
            return response.json()
    
    async def validate_app_spec(self, spec: Dict[str, Any], app_id: str = None) -> Dict[str, Any]:
        """Validate app specification"""
        async with httpx.AsyncClient() as client:
            url = f"{DO_API_BASE}/apps/propose"
            
            payload = {"spec": spec}
            if app_id:
                payload["app_id"] = app_id
            
            response = await client.post(url, headers=self.headers, json=payload)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": response.text, "status_code": response.status_code}

# Export for MCP server integration
digitalocean_tool = DigitalOceanMCPTool()

# MCP Tool Functions - Ready for revolutionary_complete.py integration
async def digitalocean_list_apps(page: int = 1, per_page: int = 20):
    """MCP Tool: List all DigitalOcean apps"""
    return await digitalocean_tool.list_apps(page, per_page)

async def digitalocean_get_app(app_id: str):
    """MCP Tool: Get DigitalOcean app details"""
    return await digitalocean_tool.get_app(app_id)

async def digitalocean_update_app(app_id: str, spec: Dict[str, Any]):
    """MCP Tool: Update DigitalOcean app configuration"""
    return await digitalocean_tool.update_app(app_id, spec)

async def digitalocean_create_app(spec: Dict[str, Any]):
    """MCP Tool: Create new DigitalOcean app"""
    return await digitalocean_tool.create_app(spec)

async def digitalocean_delete_app(app_id: str):
    """MCP Tool: Delete DigitalOcean app"""
    return await digitalocean_tool.delete_app(app_id)

async def digitalocean_create_deployment(app_id: str, force_build: bool = False):
    """MCP Tool: Create DigitalOcean deployment"""
    return await digitalocean_tool.create_deployment(app_id, force_build)

async def digitalocean_get_deployment(app_id: str, deployment_id: str):
    """MCP Tool: Get DigitalOcean deployment status"""
    return await digitalocean_tool.get_deployment(app_id, deployment_id)

async def digitalocean_list_deployments(app_id: str, page: int = 1, per_page: int = 20):
    """MCP Tool: List DigitalOcean deployments"""
    return await digitalocean_tool.list_deployments(app_id, page, per_page)

async def digitalocean_get_deployment_logs(app_id: str, deployment_id: str, component_name: str = None):
    """MCP Tool: Get DigitalOcean deployment logs"""
    return await digitalocean_tool.get_deployment_logs(app_id, deployment_id, component_name)

async def digitalocean_cancel_deployment(app_id: str, deployment_id: str):
    """MCP Tool: Cancel DigitalOcean deployment"""
    return await digitalocean_tool.cancel_deployment(app_id, deployment_id)

async def digitalocean_list_regions():
    """MCP Tool: List available DigitalOcean regions"""
    return await digitalocean_tool.list_regions()

async def digitalocean_list_instance_sizes():
    """MCP Tool: List available DigitalOcean instance sizes"""
    return await digitalocean_tool.list_instance_sizes()

async def digitalocean_validate_app_spec(spec: Dict[str, Any], app_id: str = None):
    """MCP Tool: Validate DigitalOcean app specification"""
    return await digitalocean_tool.validate_app_spec(spec, app_id)
