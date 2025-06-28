#!/usr/bin/env python3
"""
DigitalOcean MCP Server - Claude's Exact DigitalOcean Tools
Gives AI agents the same DigitalOcean capabilities Claude has
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
# DIGITALOCEAN MCP SERVER - CLAUDE'S EXACT TOOLS
# =============================================================================

app = FastAPI(title="DigitalOcean MCP Server - Claude's Tools")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
DO_TOKEN = os.getenv("DIGITALOCEAN_TOKEN", "")
MCP_PORT = int(os.getenv("MCP_PORT", "3002"))
MCP_HOST = os.getenv("MCP_HOST", "0.0.0.0")

# Tools registry
tools_registry = {}

# DigitalOcean API base URL
DO_API = "https://api.digitalocean.com/v2"

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

async def do_api_call(method: str, endpoint: str, data: Dict = None, params: Dict = None):
    """Make authenticated DigitalOcean API calls"""
    url = f"{DO_API}{endpoint}"
    headers = {
        "Authorization": f"Bearer {DO_TOKEN}",
        "Content-Type": "application/json"
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
    
    # Handle empty responses
    if response.status_code == 204:
        return {"status": "success", "message": "Operation completed"}
    
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
# CLAUDE'S EXACT DIGITALOCEAN TOOLS
# =============================================================================

# APP PLATFORM TOOLS
@mcp_tool
async def list_apps(filter_name: str = None, page: int = 1, per_page: int = 20):
    """List all apps on DigitalOcean App Platform"""
    params = {"page": page, "per_page": per_page}
    if filter_name:
        params["filter"] = filter_name
    
    return await do_api_call("GET", "/apps", params=params)

@mcp_tool
async def create_app(spec: Dict, project_id: str = None):
    """Create a new app on DigitalOcean App Platform"""
    data = {"spec": spec}
    if project_id:
        data["project_id"] = project_id
    
    return await do_api_call("POST", "/apps", data)

@mcp_tool
async def get_app(app_id: str):
    """Get app details by ID"""
    return await do_api_call("GET", f"/apps/{app_id}")

@mcp_tool
async def update_app(app_id: str, spec: Dict):
    """Update an existing app"""
    data = {"spec": spec}
    return await do_api_call("PUT", f"/apps/{app_id}", data)

@mcp_tool
async def delete_app(app_id: str):
    """Delete an app"""
    return await do_api_call("DELETE", f"/apps/{app_id}")

@mcp_tool
async def list_deployments(app_id: str, page: int = 1, per_page: int = 20):
    """List deployments for an app"""
    params = {"page": page, "per_page": per_page}
    return await do_api_call("GET", f"/apps/{app_id}/deployments", params=params)

@mcp_tool
async def create_deployment(app_id: str, force_build: bool = False):
    """Create a new deployment for an app"""
    data = {"force_build": force_build}
    return await do_api_call("POST", f"/apps/{app_id}/deployments", data)

@mcp_tool
async def get_deployment(app_id: str, deployment_id: str):
    """Get deployment details"""
    return await do_api_call("GET", f"/apps/{app_id}/deployments/{deployment_id}")

@mcp_tool
async def cancel_deployment(app_id: str, deployment_id: str):
    """Cancel a deployment"""
    return await do_api_call("POST", f"/apps/{app_id}/deployments/{deployment_id}/cancel")

@mcp_tool
async def get_deployment_logs_url(app_id: str, deployment_id: str = None, log_type: str = "BUILD"):
    """Get URL for deployment logs"""
    if deployment_id:
        endpoint = f"/apps/{app_id}/deployments/{deployment_id}/logs"
    else:
        endpoint = f"/apps/{app_id}/deployments/logs"
    
    params = {"type": log_type}
    return await do_api_call("GET", endpoint, params=params)

@mcp_tool
async def download_logs(log_url: str):
    """Download logs from the provided URL"""
    async with httpx.AsyncClient() as client:
        response = await client.get(log_url)
        return {
            "status_code": response.status_code,
            "content": response.text,
            "size": len(response.text)
        }

@mcp_tool
async def list_instance_sizes():
    """List available instance sizes for App Platform"""
    return await do_api_call("GET", "/apps/tiers/instance_sizes")

@mcp_tool
async def get_instance_size_by_slug(slug: str):
    """Get specific instance size details by slug"""
    return await do_api_call("GET", f"/apps/tiers/instance_sizes/{slug}")

@mcp_tool
async def list_app_regions():
    """List available regions for App Platform"""
    return await do_api_call("GET", "/apps/regions")

@mcp_tool
async def validate_app_spec(spec: Dict, app_id: str = None):
    """Validate an app specification"""
    data = {"spec": spec}
    if app_id:
        data["app_id"] = app_id
    
    return await do_api_call("POST", "/apps/propose", data)

@mcp_tool
async def rollback_app(app_id: str, deployment_id: str, skip_pin: bool = False):
    """Rollback app to a previous deployment"""
    data = {
        "deployment_id": deployment_id,
        "skip_pin": skip_pin
    }
    return await do_api_call("POST", f"/apps/{app_id}/rollback", data)

@mcp_tool
async def validate_app_rollback(app_id: str, deployment_id: str, skip_pin: bool = False):
    """Validate if an app can be rolled back to a specific deployment"""
    data = {
        "deployment_id": deployment_id,
        "skip_pin": skip_pin
    }
    return await do_api_call("POST", f"/apps/{app_id}/rollback/validate", data)

@mcp_tool
async def commit_app_rollback(app_id: str):
    """Commit an app rollback"""
    return await do_api_call("POST", f"/apps/{app_id}/rollback/commit")

@mcp_tool
async def revert_app_rollback(app_id: str):
    """Revert an app rollback"""
    return await do_api_call("POST", f"/apps/{app_id}/rollback/revert")

# DATABASE TOOLS
@mcp_tool
async def get_database_options():
    """Get available database options"""
    return await do_api_call("GET", "/databases/options")

@mcp_tool
async def list_databases():
    """List all database clusters"""
    return await do_api_call("GET", "/databases")

@mcp_tool
async def create_database_cluster(name: str, engine: str, size: str, region: str, num_nodes: int = 1, version: str = None):
    """Create a new database cluster"""
    data = {
        "name": name,
        "engine": engine,
        "size": size,
        "region": region,
        "num_nodes": num_nodes
    }
    if version:
        data["version"] = version
    
    return await do_api_call("POST", "/databases", data)

@mcp_tool
async def get_database_cluster(database_id: str):
    """Get database cluster details"""
    return await do_api_call("GET", f"/databases/{database_id}")

@mcp_tool
async def delete_database_cluster(database_id: str):
    """Delete a database cluster"""
    return await do_api_call("DELETE", f"/databases/{database_id}")

@mcp_tool
async def list_database_firewall_rules(database_id: str):
    """List firewall rules for a database cluster"""
    return await do_api_call("GET", f"/databases/{database_id}/firewall")

@mcp_tool
async def update_database_firewall_rules(database_id: str, rules: List[Dict]):
    """Update firewall rules for a database cluster"""
    data = {"rules": rules}
    return await do_api_call("PUT", f"/databases/{database_id}/firewall", data)

@mcp_tool
async def list_database_cluster_users(database_id: str):
    """List users for a database cluster"""
    return await do_api_call("GET", f"/databases/{database_id}/users")

@mcp_tool
async def create_database_user(database_id: str, name: str, mysql_settings: Dict = None):
    """Create a new database user"""
    data = {"name": name}
    if mysql_settings:
        data["mysql_settings"] = mysql_settings
    
    return await do_api_call("POST", f"/databases/{database_id}/users", data)

@mcp_tool
async def get_database_user(database_id: str, username: str):
    """Get database user details"""
    return await do_api_call("GET", f"/databases/{database_id}/users/{username}")

@mcp_tool
async def delete_database_user(database_id: str, username: str):
    """Delete a database user"""
    return await do_api_call("DELETE", f"/databases/{database_id}/users/{username}")

@mcp_tool
async def list_database_cluster_databases(database_id: str):
    """List databases in a cluster"""
    return await do_api_call("GET", f"/databases/{database_id}/dbs")

@mcp_tool
async def create_database(database_id: str, name: str):
    """Create a new database in cluster"""
    data = {"name": name}
    return await do_api_call("POST", f"/databases/{database_id}/dbs", data)

@mcp_tool
async def get_database(database_id: str, db_name: str):
    """Get database details"""
    return await do_api_call("GET", f"/databases/{database_id}/dbs/{db_name}")

@mcp_tool
async def delete_database(database_id: str, db_name: str):
    """Delete a database"""
    return await do_api_call("DELETE", f"/databases/{database_id}/dbs/{db_name}")

@mcp_tool
async def get_database_cluster_certificate(database_id: str):
    """Get database cluster certificate"""
    return await do_api_call("GET", f"/databases/{database_id}/ca")

# DROPLET TOOLS
@mcp_tool
async def list_droplets(page: int = 1, per_page: int = 20, name: str = None, tag_name: str = None):
    """List all Droplets"""
    params = {"page": page, "per_page": per_page}
    if name:
        params["name"] = name
    if tag_name:
        params["tag_name"] = tag_name
    
    return await do_api_call("GET", "/droplets", params=params)

@mcp_tool
async def create_droplet(name: str, region: str, size: str, image: str, ssh_keys: List[str] = None, backups: bool = False, ipv6: bool = False, monitoring: bool = False):
    """Create a new Droplet"""
    data = {
        "name": name,
        "region": region,
        "size": size,
        "image": image,
        "backups": backups,
        "ipv6": ipv6,
        "monitoring": monitoring
    }
    if ssh_keys:
        data["ssh_keys"] = ssh_keys
    
    return await do_api_call("POST", "/droplets", data)

@mcp_tool
async def get_droplet(droplet_id: str):
    """Get Droplet details by ID"""
    return await do_api_call("GET", f"/droplets/{droplet_id}")

@mcp_tool
async def delete_droplet(droplet_id: str):
    """Delete a Droplet"""
    return await do_api_call("DELETE", f"/droplets/{droplet_id}")

@mcp_tool
async def power_on_droplet(droplet_id: str):
    """Power on a Droplet"""
    data = {"action": "power_on"}
    return await do_api_call("POST", f"/droplets/{droplet_id}/actions", data)

@mcp_tool
async def power_off_droplet(droplet_id: str):
    """Power off a Droplet"""
    data = {"action": "power_off"}
    return await do_api_call("POST", f"/droplets/{droplet_id}/actions", data)

@mcp_tool
async def reboot_droplet(droplet_id: str):
    """Reboot a Droplet"""
    data = {"action": "reboot"}
    return await do_api_call("POST", f"/droplets/{droplet_id}/actions", data)

@mcp_tool
async def resize_droplet(droplet_id: str, size: str, disk: bool = False):
    """Resize a Droplet"""
    data = {
        "action": "resize",
        "size": size,
        "disk": disk
    }
    return await do_api_call("POST", f"/droplets/{droplet_id}/actions", data)

@mcp_tool
async def snapshot_droplet(droplet_id: str, name: str):
    """Create snapshot of Droplet"""
    data = {
        "action": "snapshot",
        "name": name
    }
    return await do_api_call("POST", f"/droplets/{droplet_id}/actions", data)

# KUBERNETES TOOLS
@mcp_tool
async def list_kubernetes_clusters():
    """List all Kubernetes clusters"""
    return await do_api_call("GET", "/kubernetes/clusters")

@mcp_tool
async def create_kubernetes_cluster(name: str, region: str, version: str, node_pools: List[Dict]):
    """Create a new Kubernetes cluster"""
    data = {
        "name": name,
        "region": region,
        "version": version,
        "node_pools": node_pools
    }
    return await do_api_call("POST", "/kubernetes/clusters", data)

@mcp_tool
async def get_kubernetes_cluster(cluster_id: str):
    """Get Kubernetes cluster details"""
    return await do_api_call("GET", f"/kubernetes/clusters/{cluster_id}")

@mcp_tool
async def delete_kubernetes_cluster(cluster_id: str):
    """Delete a Kubernetes cluster"""
    return await do_api_call("DELETE", f"/kubernetes/clusters/{cluster_id}")

@mcp_tool
async def get_kubernetes_kubeconfig(cluster_id: str):
    """Get kubeconfig for cluster"""
    return await do_api_call("GET", f"/kubernetes/clusters/{cluster_id}/kubeconfig")

# SPACES TOOLS
@mcp_tool
async def list_spaces():
    """List all Spaces"""
    return await do_api_call("GET", "/spaces")

@mcp_tool
async def create_space(name: str, region: str):
    """Create a new Space"""
    data = {
        "name": name,
        "region": region
    }
    return await do_api_call("POST", "/spaces", data)

@mcp_tool
async def get_space(space_name: str):
    """Get Space details"""
    return await do_api_call("GET", f"/spaces/{space_name}")

@mcp_tool
async def delete_space(space_name: str):
    """Delete a Space"""
    return await do_api_call("DELETE", f"/spaces/{space_name}")

# LOAD BALANCER TOOLS
@mcp_tool
async def list_load_balancers():
    """List all Load Balancers"""
    return await do_api_call("GET", "/load_balancers")

@mcp_tool
async def create_load_balancer(name: str, algorithm: str, region: str, forwarding_rules: List[Dict], droplet_ids: List[str] = None):
    """Create a new Load Balancer"""
    data = {
        "name": name,
        "algorithm": algorithm,
        "region": region,
        "forwarding_rules": forwarding_rules
    }
    if droplet_ids:
        data["droplet_ids"] = droplet_ids
    
    return await do_api_call("POST", "/load_balancers", data)

@mcp_tool
async def get_load_balancer(lb_id: str):
    """Get Load Balancer details"""
    return await do_api_call("GET", f"/load_balancers/{lb_id}")

@mcp_tool
async def delete_load_balancer(lb_id: str):
    """Delete a Load Balancer"""
    return await do_api_call("DELETE", f"/load_balancers/{lb_id}")

# DOMAIN TOOLS
@mcp_tool
async def list_domains():
    """List all domains"""
    return await do_api_call("GET", "/domains")

@mcp_tool
async def create_domain(name: str, ip_address: str = None):
    """Create a new domain"""
    data = {"name": name}
    if ip_address:
        data["ip_address"] = ip_address
    
    return await do_api_call("POST", "/domains", data)

@mcp_tool
async def get_domain(domain_name: str):
    """Get domain details"""
    return await do_api_call("GET", f"/domains/{domain_name}")

@mcp_tool
async def delete_domain(domain_name: str):
    """Delete a domain"""
    return await do_api_call("DELETE", f"/domains/{domain_name}")

@mcp_tool
async def list_domain_records(domain_name: str):
    """List domain records"""
    return await do_api_call("GET", f"/domains/{domain_name}/records")

@mcp_tool
async def create_domain_record(domain_name: str, record_type: str, name: str, data: str, priority: int = None, port: int = None, ttl: int = 1800, weight: int = None, flags: int = None, tag: str = None):
    """Create a new domain record"""
    record_data = {
        "type": record_type,
        "name": name,
        "data": data,
        "ttl": ttl
    }
    
    if priority is not None:
        record_data["priority"] = priority
    if port is not None:
        record_data["port"] = port
    if weight is not None:
        record_data["weight"] = weight
    if flags is not None:
        record_data["flags"] = flags
    if tag is not None:
        record_data["tag"] = tag
    
    return await do_api_call("POST", f"/domains/{domain_name}/records", record_data)

@mcp_tool
async def get_domain_record(domain_name: str, record_id: str):
    """Get domain record details"""
    return await do_api_call("GET", f"/domains/{domain_name}/records/{record_id}")

@mcp_tool
async def update_domain_record(domain_name: str, record_id: str, record_type: str = None, name: str = None, data: str = None, priority: int = None, port: int = None, ttl: int = None, weight: int = None, flags: int = None, tag: str = None):
    """Update a domain record"""
    record_data = {}
    
    if record_type is not None:
        record_data["type"] = record_type
    if name is not None:
        record_data["name"] = name
    if data is not None:
        record_data["data"] = data
    if priority is not None:
        record_data["priority"] = priority
    if port is not None:
        record_data["port"] = port
    if ttl is not None:
        record_data["ttl"] = ttl
    if weight is not None:
        record_data["weight"] = weight
    if flags is not None:
        record_data["flags"] = flags
    if tag is not None:
        record_data["tag"] = tag
    
    return await do_api_call("PUT", f"/domains/{domain_name}/records/{record_id}", record_data)

@mcp_tool
async def delete_domain_record(domain_name: str, record_id: str):
    """Delete a domain record"""
    return await do_api_call("DELETE", f"/domains/{domain_name}/records/{record_id}")

# ACCOUNT TOOLS
@mcp_tool
async def get_account():
    """Get account information"""
    return await do_api_call("GET", "/account")

@mcp_tool
async def get_balance():
    """Get account balance"""
    return await do_api_call("GET", "/customers/my/balance")

@mcp_tool
async def list_billing_history():
    """List billing history"""
    return await do_api_call("GET", "/customers/my/billing_history")

# PROJECT TOOLS
@mcp_tool
async def list_projects():
    """List all projects"""
    return await do_api_call("GET", "/projects")

@mcp_tool
async def create_project(name: str, description: str = "", purpose: str = "Web Application", environment: str = "Production"):
    """Create a new project"""
    data = {
        "name": name,
        "description": description,
        "purpose": purpose,
        "environment": environment
    }
    return await do_api_call("POST", "/projects", data)

@mcp_tool
async def get_project(project_id: str):
    """Get project details"""
    return await do_api_call("GET", f"/projects/{project_id}")

@mcp_tool
async def update_project(project_id: str, name: str = None, description: str = None, purpose: str = None, environment: str = None, is_default: bool = None):
    """Update a project"""
    data = {}
    if name is not None:
        data["name"] = name
    if description is not None:
        data["description"] = description
    if purpose is not None:
        data["purpose"] = purpose
    if environment is not None:
        data["environment"] = environment
    if is_default is not None:
        data["is_default"] = is_default
    
    return await do_api_call("PUT", f"/projects/{project_id}", data)

@mcp_tool
async def delete_project(project_id: str):
    """Delete a project"""
    return await do_api_call("DELETE", f"/projects/{project_id}")

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
        "name": "DigitalOcean MCP Server",
        "description": "Claude's exact DigitalOcean tools for AI agents",
        "version": "1.0",
        "status": "operational",
        "tools_count": len(tools_registry),
        "capabilities": [
            "App Platform management",
            "Database clusters",
            "Droplet management", 
            "Kubernetes clusters",
            "Load balancers",
            "Domains and DNS",
            "Spaces storage",
            "Account management"
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
        # Test DigitalOcean API connection
        account = await get_account()
        return {
            "status": "healthy",
            "digitalocean_api": "connected",
            "account_email": account.get("account", {}).get("email", "unknown"),
            "tools_loaded": len(tools_registry),
            "timestamp": datetime.now().isoformat()
        }
    except:
        return {
            "status": "healthy",
            "digitalocean_api": "disconnected",
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
    
    print(f"🌊 Starting DigitalOcean MCP Server - Claude's Tools")
    print(f"📍 Host: {MCP_HOST}")
    print(f"🔌 Port: {MCP_PORT}")
    print(f"🔧 DigitalOcean Tools: {len(tools_registry)}")
    print(f"🔑 DO Token: {'✅ Set' if DO_TOKEN else '❌ Missing'}")
    print(f"✅ Server ready!")
    
    uvicorn.run(app, host=MCP_HOST, port=MCP_PORT)
