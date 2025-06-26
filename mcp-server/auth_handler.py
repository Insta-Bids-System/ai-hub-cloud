#!/usr/bin/env python3
"""
OAuth Authentication Handler for MCP Server
Handles authentication for remote Claude Desktop connections
"""

import os
import secrets
import json
from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import jwt, JWTError
import redis.asyncio as redis

# Configuration
SECRET_KEY = os.getenv("OAUTH_CLIENT_SECRET", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

class AuthHandler:
    def __init__(self):
        self.redis_client = None
    
    async def get_redis(self):
        """Get or create Redis connection"""
        if self.redis_client is None:
            self.redis_client = await redis.from_url(REDIS_URL, decode_responses=True)
        return self.redis_client
    
    async def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "iat": datetime.utcnow()})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        
        # Store token in Redis for validation
        r = await self.get_redis()
        await r.setex(
            f"ai-hub:token:{encoded_jwt[:20]}",
            int(expires_delta.total_seconds() if expires_delta else ACCESS_TOKEN_EXPIRE_MINUTES * 60),
            json.dumps({
                "full_token": encoded_jwt,
                "data": data,
                "expires": expire.isoformat()
            })
        )
        
        return encoded_jwt
    
    async def verify_token(self, token: str) -> Optional[Dict]:
        """Verify JWT token"""
        try:
            # Decode token
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            
            # Check if token exists in Redis
            r = await self.get_redis()
            token_data = await r.get(f"ai-hub:token:{token[:20]}")
            
            if not token_data:
                return None
            
            stored_data = json.loads(token_data)
            if stored_data["full_token"] != token:
                return None
            
            return payload
            
        except JWTError:
            return None
    
    async def generate_client_token(self, client_id: str, client_name: str = "Claude Desktop") -> str:
        """Generate a token for Claude Desktop client"""
        token_data = {
            "client_id": client_id,
            "client_name": client_name,
            "type": "mcp_client",
            "created": datetime.utcnow().isoformat()
        }
        
        # Create token with 30 day expiry for desktop clients
        token = await self.create_access_token(
            token_data,
            expires_delta=timedelta(days=30)
        )
        
        # Store client info
        r = await self.get_redis()
        await r.hset(
            "ai-hub:clients",
            client_id,
            json.dumps({
                "name": client_name,
                "token_prefix": token[:20],
                "created": datetime.utcnow().isoformat(),
                "last_seen": datetime.utcnow().isoformat()
            })
        )
        
        return token
    
    async def validate_request(self, auth_header: Optional[str]) -> Optional[Dict]:
        """Validate incoming request authentication"""
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        
        token = auth_header.replace("Bearer ", "")
        return await self.verify_token(token)
    
    async def update_client_activity(self, client_id: str):
        """Update last seen time for client"""
        r = await self.get_redis()
        client_data = await r.hget("ai-hub:clients", client_id)
        
        if client_data:
            data = json.loads(client_data)
            data["last_seen"] = datetime.utcnow().isoformat()
            await r.hset("ai-hub:clients", client_id, json.dumps(data))
    
    async def revoke_token(self, token: str):
        """Revoke a token"""
        r = await self.get_redis()
        await r.delete(f"ai-hub:token:{token[:20]}")
    
    async def list_active_clients(self) -> Dict[str, Dict]:
        """List all active clients"""
        r = await self.get_redis()
        clients = await r.hgetall("ai-hub:clients")
        
        active_clients = {}
        for client_id, client_data in clients.items():
            data = json.loads(client_data)
            # Consider active if seen in last 7 days
            last_seen = datetime.fromisoformat(data["last_seen"])
            if datetime.utcnow() - last_seen < timedelta(days=7):
                active_clients[client_id] = data
        
        return active_clients

# Middleware for MCP server
async def auth_middleware(handler):
    """Wrapper to add authentication to MCP handlers"""
    auth = AuthHandler()
    
    async def authenticated_handler(request):
        # For now, we'll implement basic token validation
        # In production, this would integrate with the MCP server
        auth_header = request.headers.get("Authorization")
        
        if not auth_header:
            # For initial setup, allow local connections
            if request.remote == "127.0.0.1" or request.remote == "::1":
                return await handler(request)
            else:
                return {"error": "Authentication required"}
        
        client_data = await auth.validate_request(auth_header)
        if not client_data:
            return {"error": "Invalid authentication"}
        
        # Update activity
        await auth.update_client_activity(client_data["client_id"])
        
        # Add client info to request
        request.client_data = client_data
        
        return await handler(request)
    
    return authenticated_handler

# CLI for generating tokens
if __name__ == "__main__":
    import asyncio
    import sys
    
    async def main():
        if len(sys.argv) < 2:
            print("Usage: python auth_handler.py generate-token [client-name]")
            sys.exit(1)
        
        command = sys.argv[1]
        
        if command == "generate-token":
            client_name = sys.argv[2] if len(sys.argv) > 2 else "Claude Desktop"
            client_id = f"client_{secrets.token_urlsafe(16)}"
            
            auth = AuthHandler()
            token = await auth.generate_client_token(client_id, client_name)
            
            print(f"""
✅ Token generated successfully!

Client ID: {client_id}
Client Name: {client_name}
Token: {token}

Add this to your Claude Desktop configuration:
{{
  "mcpServers": {{
    "instabids-cloud": {{
      "command": "npx",
      "args": ["-y", "mcp-remote-client"],
      "env": {{
        "MCP_ENDPOINT": "https://your-domain.com/mcp",
        "MCP_API_KEY": "{token}"
      }}
    }}
  }}
}}
""")
            
            # Close Redis connection
            if auth.redis_client:
                await auth.redis_client.close()
    
    asyncio.run(main())
