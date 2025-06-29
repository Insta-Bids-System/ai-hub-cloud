#!/usr/bin/env python3
"""
Remote Execution MCP Server
Runs on the droplet and accepts commands from Claude
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import subprocess
import os
import asyncio
from typing import Optional
import logging

app = FastAPI(title="Droplet Remote Executor")

class CommandRequest(BaseModel):
    command: str
    cwd: Optional[str] = None
    timeout: Optional[int] = 300

class CommandResponse(BaseModel):
    stdout: str
    stderr: str
    return_code: int
    success: bool

# Security token - CHANGE THIS!
API_TOKEN = os.getenv("EXECUTOR_API_TOKEN", "your-secret-token-here")

@app.post("/execute")
async def execute_command(request: CommandRequest, token: str = None):
    """Execute a shell command on the droplet"""
    # Basic auth check
    if token != API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    try:
        # Run command
        process = await asyncio.create_subprocess_shell(
            request.command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=request.cwd
        )
        
        # Wait for completion with timeout
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=request.timeout
            )
        except asyncio.TimeoutError:
            process.kill()
            return CommandResponse(
                stdout="",
                stderr="Command timed out",
                return_code=-1,
                success=False
            )
        
        return CommandResponse(
            stdout=stdout.decode() if stdout else "",
            stderr=stderr.decode() if stderr else "",
            return_code=process.returncode,
            success=process.returncode == 0
        )
        
    except Exception as e:
        return CommandResponse(
            stdout="",
            stderr=str(e),
            return_code=-1,
            success=False
        )

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "droplet-executor"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9999)
