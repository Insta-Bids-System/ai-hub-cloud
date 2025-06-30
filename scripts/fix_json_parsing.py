#!/usr/bin/env python3
"""
Emergency JSON Parsing Fix for MCP Server
This script updates the main.py to handle Open WebUI's request format
"""

import os
import shutil
from datetime import datetime

# Path to the main.py file
MAIN_PY_PATH = "/root/ai-hub-cloud/mcp-server/main.py"
BACKUP_PATH = f"/root/ai-hub-cloud/mcp-server/main.py.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# The fix to insert after imports
JSON_FIX = '''
# JSON PARSING FIX - Handle Open WebUI request formats
async def parse_request_data(request: Request):
    """Parse request data from various formats"""
    try:
        # Log request details for debugging
        content_type = request.headers.get('content-type', '')
        print(f"[MCP] Request Content-Type: {content_type}")
        
        # Try to get raw body first
        body = await request.body()
        print(f"[MCP] Raw body: {body[:200]}...")  # First 200 chars
        
        # Handle different content types
        if 'application/x-www-form-urlencoded' in content_type:
            # Form data
            form_data = await request.form()
            data = dict(form_data)
            print(f"[MCP] Parsed form data: {data}")
        elif 'multipart/form-data' in content_type:
            # Multipart form
            form_data = await request.form()
            data = dict(form_data)
            print(f"[MCP] Parsed multipart data: {data}")
        else:
            # Try JSON
            data = await request.json()
            print(f"[MCP] Parsed JSON data: {data}")
        
        return data
    except Exception as e:
        print(f"[MCP] Error parsing request: {e}")
        # Try to decode body as string
        try:
            body_str = body.decode('utf-8')
            print(f"[MCP] Body as string: {body_str}")
        except:
            pass
        raise
'''

def update_main_py():
    """Update the main.py file with the JSON parsing fix"""
    print(f"Backing up {MAIN_PY_PATH} to {BACKUP_PATH}")
    shutil.copy2(MAIN_PY_PATH, BACKUP_PATH)
    
    print("Reading main.py...")
    with open(MAIN_PY_PATH, 'r') as f:
        content = f.read()
    
    # Check if fix already applied
    if "parse_request_data" in content:
        print("Fix already applied!")
        return
    
    # Find where to insert the fix (after imports)
    import_end = content.find("app = FastAPI")
    if import_end == -1:
        import_end = content.find("# Helper function")
    
    # Insert the fix
    new_content = content[:import_end] + JSON_FIX + "\n" + content[import_end:]
    
    # Update the mcp_call function to use the new parser
    new_content = new_content.replace(
        "data = await request.json()",
        "data = await parse_request_data(request)"
    )
    
    # Add error handling to show available tools
    new_content = new_content.replace(
        'raise HTTPException(status_code=404, detail=f"Tool \'{tool_name}\' not found")',
        'available_tools = list(tools_registry.keys())[:10]\n        raise HTTPException(status_code=404, detail=f"Tool \'{tool_name}\' not found. Available tools: {available_tools}...")'
    )
    
    print("Writing updated main.py...")
    with open(MAIN_PY_PATH, 'w') as f:
        f.write(new_content)
    
    print("Fix applied successfully!")

def add_test_endpoint():
    """Add a test endpoint to main.py"""
    with open(MAIN_PY_PATH, 'r') as f:
        content = f.read()
    
    if "/mcp/test/" in content:
        print("Test endpoint already exists")
        return
    
    # Add test endpoint before the last line
    test_endpoint = '''
@app.post("/mcp/test/{tool_name}")
async def test_tool(tool_name: str, request: Request):
    """Test endpoint for debugging"""
    try:
        if tool_name not in tools_registry:
            return {"error": f"Tool '{tool_name}' not found", "available": list(tools_registry.keys())[:20]}
        
        # Parse any parameters
        try:
            data = await parse_request_data(request)
            parameters = data.get("parameters", {})
        except:
            parameters = {}
        
        # Execute tool
        tool = tools_registry[tool_name]
        result = await tool["function"](**parameters)
        
        return {"status": "success", "tool": tool_name, "result": result}
    except Exception as e:
        return {"status": "error", "tool": tool_name, "error": str(e)}
'''
    
    # Insert before the last line
    last_line_start = content.rfind("if __name__")
    new_content = content[:last_line_start] + test_endpoint + "\n\n" + content[last_line_start:]
    
    with open(MAIN_PY_PATH, 'w') as f:
        f.write(new_content)
    
    print("Test endpoint added!")

if __name__ == "__main__":
    print("Applying JSON parsing fix to MCP server...")
    update_main_py()
    add_test_endpoint()
    print("\nNow restart the MCP server:")
    print("docker restart mcp-server")
    print("\nThen test with:")
    print("curl -X POST http://localhost:8888/mcp/test/get_health -H 'Content-Type: application/json' -d '{}'")
