import asyncio
import websockets
import json

async def kickoff():
    uri = "ws://localhost:8000/ws/self-build?token=neurex-dev-token"
    async with websockets.connect(uri) as websocket:
        msg = {
            "type": "message",
            "content": "Self-Improvement Task: Implement a Human-in-the-loop Shell Approval workflow.\n\n"
                       "Requirements:\n"
                       "1. Update the 'terminal' MCP tool in 'core/mcp/tools/terminal.py' to detect 'unsafe' commands (rm, mv, docker, etc).\n"
                       "2. If a command is unsafe, return a structured status 'AWAITING_SHELL_APPROVAL'.\n"
                       "3. Update the frontend 'AgentTerminal' component to show an [Approve/Deny] button when a shell command is pending.\n"
                       "4. Ensure the Orchestrator can resume the task once the user approves.\n\n"
                       "Start by planning the implementation."
        }
        await websocket.send(json.dumps(msg))
        print("Message sent to Neurex Orchestrator.")
        
        # Listen for the plan
        while True:
            response = await websocket.recv()
            data = json.loads(response)
            if data.get("event") == "plan_ready":
                print("Neurex has generated a plan!")
                print(json.dumps(data["data"], indent=2))
                break
            elif data.get("event") == "token":
                print(data["data"], end="", flush=True)

if __name__ == "__main__":
    asyncio.run(kickoff())
