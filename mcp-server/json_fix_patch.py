#!/usr/bin/env python3
"""
MCP Server JSON Fix - Apply this patch to fix Open WebUI integration
"""

# This shows the key changes needed in main.py to fix the JSON parsing error

# CHANGE 1: Import additional modules
import traceback
import urllib.parse

# CHANGE 2: Replace the mcp_call function with this fixed version:
"""
@app.post("/mcp/call")
async def mcp_call(request: Request):
    \"\"\"Main MCP tool calling endpoint - Fixed for Open WebUI integration\"\"\"
    tool_name = None
    try:
        # Debug logging
        content_type = request.headers.get('content-type', '')
        print(f"[MCP] Content-Type: {content_type}")
        
        # Try to get raw body for debugging
        body = await request.body()
        print(f"[MCP] Raw body: {body[:200]}...")  # First 200 chars
        
        # Parse request based on content type
        if 'application/json' in content_type:
            try:
                data = json.loads(body)
            except json.JSONDecodeError as e:
                print(f"[MCP] JSON decode error: {e}")
                # Try to extract from form-encoded data
                data = {}
        elif 'application/x-www-form-urlencoded' in content_type:
            # Handle form data from Open WebUI
            form_data = urllib.parse.parse_qs(body.decode('utf-8'))
            print(f"[MCP] Form data: {form_data}")
            
            # Extract tool and parameters from form data
            data = {}
            if 'tool' in form_data:
                data['tool'] = form_data['tool'][0]
            if 'parameters' in form_data:
                try:
                    data['parameters'] = json.loads(form_data['parameters'][0])
                except:
                    data['parameters'] = {}
        else:
            # Try to parse as JSON anyway
            try:
                data = json.loads(body)
            except:
                print(f"[MCP] Unable to parse body as JSON")
                data = {}
        
        print(f"[MCP] Parsed data: {data}")
        
        # Extract tool name and parameters
        tool_name = data.get("tool")
        parameters = data.get("parameters", {})
        
        if not tool_name:
            # Check if it's in a different format (e.g., OpenWebUI might send it differently)
            if "function" in data:
                tool_name = data["function"]
            elif "name" in data:
                tool_name = data["name"]
            else:
                raise HTTPException(status_code=400, detail="No tool name provided")
        
        print(f"[MCP] Tool: {tool_name}, Parameters: {parameters}")
        
        if tool_name not in tools_registry:
            available_tools = list(tools_registry.keys())
            raise HTTPException(
                status_code=404, 
                detail=f"Tool '{tool_name}' not found. Available tools: {available_tools}"
            )
        
        tool = tools_registry[tool_name]
        result = await tool["function"](**parameters)
        
        print(f"[MCP] Tool executed successfully: {tool_name}")
        
        return {
            "status": "success",
            "tool": tool_name,
            "result": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        error_detail = f"Error executing tool '{tool_name}': {str(e)}\\n{traceback.format_exc()}"
        print(f"[MCP] {error_detail}")
        return {
            "status": "error",
            "tool": tool_name,
            "error": str(e),
            "detail": error_detail
        }
"""

# CHANGE 3: Add a debug endpoint for testing:
"""
@app.post("/mcp/test/{tool_name}")
async def test_tool(tool_name: str, request: Request):
    \"\"\"Test endpoint for debugging tool calls\"\"\"
    try:
        body = await request.json()
        parameters = body.get("parameters", {})
        
        if tool_name not in tools_registry:
            return {"error": f"Tool '{tool_name}' not found", "available": list(tools_registry.keys())}
        
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
            "error": str(e),
            "trace": traceback.format_exc()
        }
"""

# The key fixes are:
# 1. Handle both JSON and form-encoded data
# 2. Add debug logging to see what Open WebUI sends
# 3. Try multiple field names for tool (tool, function, name)
# 4. Better error messages showing available tools
# 5. Debug endpoint for direct testing
