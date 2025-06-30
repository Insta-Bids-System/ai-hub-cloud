#!/usr/bin/env python3
"""
Quick fix for MCP server JSON parsing issue
Run this on the droplet to fix the issue
"""

import os
import re

# Read the main.py file
with open('/root/ai-hub-cloud/mcp-server/main.py', 'r') as f:
    content = f.read()

# Check if already fixed
if 'traceback' in content and 'urllib.parse' in content:
    print("✅ File already contains the fix!")
    exit(0)

# Add imports if not present
if 'import traceback' not in content:
    content = content.replace('import os', 'import os\nimport traceback')
if 'import urllib' not in content:
    content = content.replace('import os', 'import os\nimport urllib.parse')

# Create the new mcp_call function
new_mcp_call = '''@app.post("/mcp/call")
async def mcp_call(request: Request):
    """Main MCP tool calling endpoint - Fixed for Open WebUI"""
    tool_name = None
    try:
        content_type = request.headers.get('content-type', '')
        body = await request.body()
        
        # Parse based on content type
        if 'application/json' in content_type:
            try:
                data = json.loads(body)
            except:
                data = {}
        elif 'application/x-www-form-urlencoded' in content_type:
            form_data = urllib.parse.parse_qs(body.decode('utf-8'))
            data = {}
            if 'tool' in form_data:
                data['tool'] = form_data['tool'][0]
            if 'parameters' in form_data:
                try:
                    data['parameters'] = json.loads(form_data['parameters'][0])
                except:
                    data['parameters'] = {}
        else:
            try:
                data = json.loads(body)
            except:
                data = {}
        
        tool_name = data.get("tool") or data.get("function") or data.get("name")
        parameters = data.get("parameters", {})
        
        if not tool_name:
            raise HTTPException(status_code=400, detail="No tool name provided")
        
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
        }'''

# Replace the mcp_call function
pattern = r'@app\.post\("/mcp/call"\)[\s\S]*?(?=@app\.|if __name__|$)'
content = re.sub(pattern, new_mcp_call + '\n\n', content)

# Write back
with open('/root/ai-hub-cloud/mcp-server/main.py', 'w') as f:
    f.write(content)

print("✅ Fixed main.py!")

# Now restart the service
os.system('cd /root/ai-hub-cloud && docker-compose -f docker-compose.full.yml restart mcp-server')
print("✅ MCP Server restarted!")

# Test the fix
import time
time.sleep(5)
os.system('curl -X POST http://localhost/mcp/test/get_health -H "Content-Type: application/json" -d \'{"parameters": {}}\'')
