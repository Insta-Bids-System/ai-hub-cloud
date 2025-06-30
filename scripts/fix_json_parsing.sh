#!/bin/bash
# Fix JSON Parsing Issue in MCP Server
# Run this on the droplet to fix Open WebUI integration

echo "🔧 Fixing MCP Server JSON Parsing Issue..."

cd /root/ai-hub-cloud

# Backup current main.py
echo "📦 Backing up current main.py..."
cp mcp-server/main.py mcp-server/main.py.backup.$(date +%Y%m%d_%H%M%S)

# Apply the fix by modifying main.py
echo "🛠️ Applying JSON parsing fix..."

# Add imports at the top
sed -i '12a import traceback\nimport urllib.parse' mcp-server/main.py

# Replace the mcp_call function with the fixed version
cat > /tmp/mcp_call_fix.py << 'EOF'
@app.post("/mcp/call")
async def mcp_call(request: Request):
    """Main MCP tool calling endpoint - Fixed for Open WebUI integration"""
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
        error_detail = f"Error executing tool '{tool_name}': {str(e)}\n{traceback.format_exc()}"
        print(f"[MCP] {error_detail}")
        return {
            "status": "error",
            "tool": tool_name,
            "error": str(e),
            "detail": error_detail
        }
EOF

# Use Python to replace the function
python3 << 'PYTHON_SCRIPT'
import re

# Read the current file
with open('mcp-server/main.py', 'r') as f:
    content = f.read()

# Read the new function
with open('/tmp/mcp_call_fix.py', 'r') as f:
    new_function = f.read()

# Replace the mcp_call function
pattern = r'@app\.post\("/mcp/call"\)\s*async def mcp_call.*?(?=@app\.|if __name__|$)'
content = re.sub(pattern, new_function + '\n\n', content, flags=re.DOTALL)

# Write back
with open('mcp-server/main.py', 'w') as f:
    f.write(content)

print("✅ Function replaced successfully")
PYTHON_SCRIPT

# Add debug endpoint before the SSE endpoint
echo "🔍 Adding debug endpoint..."
sed -i '/# SSE endpoint for Claude Desktop/i\
# Debug endpoint to test tools directly\
@app.post("/mcp/test/{tool_name}")\
async def test_tool(tool_name: str, request: Request):\
    """Test endpoint for debugging tool calls"""\
    try:\
        body = await request.json()\
        parameters = body.get("parameters", {})\
        \
        if tool_name not in tools_registry:\
            return {"error": f"Tool \'{tool_name}\' not found", "available": list(tools_registry.keys())}\
        \
        tool = tools_registry[tool_name]\
        result = await tool["function"](**parameters)\
        \
        return {\
            "status": "success",\
            "tool": tool_name,\
            "result": result\
        }\
    except Exception as e:\
        return {\
            "status": "error",\
            "tool": tool_name,\
            "error": str(e),\
            "trace": traceback.format_exc()\
        }\
\
' mcp-server/main.py

# Update version number
sed -i 's/"version": "1.0"/"version": "1.1"/' mcp-server/main.py

# Rebuild and restart the MCP server
echo "🔄 Rebuilding MCP server..."
docker-compose -f docker-compose.full.yml build mcp-server

echo "🚀 Restarting MCP server..."
docker-compose -f docker-compose.full.yml restart mcp-server

# Show logs
echo "📋 Showing MCP server logs..."
docker logs mcp-server --tail 20

echo "✅ JSON parsing fix applied!"
echo ""
echo "🧪 Test the fix with:"
echo "curl -X POST http://159.65.36.162/mcp/test/get_health \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"parameters\": {}}'"
