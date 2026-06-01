# scratch/test_real_hitl.py
import os
import sys
import asyncio
from pathlib import Path

# Add project modules to system path
sys.path.insert(0, str(Path(__file__).parent.parent / "neurex-api"))

from core.database.connection import get_async_session_context
from core.context.manager import ContextManager
from core.context.rules_parser import RulesParser
from core.orchestrator import Orchestrator
from core.task_graph import get_graph
from core.security.governance import governance_manager

async def run_live_test():
    print("🎬 Starting Real HITL E2E Test Sequence...")
    
    # 1. Setup execution variables
    os.environ["NEUREX_MOCK_LLM"] = "true"
    os.environ["WORKSPACE_PATH"] = "/tmp/neurex-live-test-workspace"
    os.environ["AUTONOMY_CEILING"] = "limited"
    
    workspace = Path("/tmp/neurex-live-test-workspace")
    workspace.mkdir(parents=True, exist_ok=True)
    
    test_file = workspace / "hello.py"
    if test_file.exists():
        test_file.unlink()
        
    governance_manager.dynamic_grants["live-hitl-conv"] = {""}
    
    # 2. Open DB and start session
    async with get_async_session_context() as db_session:
        rules = RulesParser()
        ctx = ContextManager()
        orch = Orchestrator(db_session, rules, ctx)
        
        # Phase 1: Planning
        print("\n[Phase 1] Launching plan decomposition...")
        events = []
        async for event in orch.run("Create a file named hello.py", "live-hitl-conv"):
            events.append(event)
            print(f" -> Event: {event['event']}")
            
        plan_ready = next((e for e in events if e["event"] == "plan_ready"), None)
        if not plan_ready:
            print("❌ FAILURE: No plan_ready event generated!")
            return
            
        graph_id = plan_ready["data"]["graph_id"]
        print(f"✅ Success: Plan generated. Graph ID: {graph_id}")
        
        # Verify DB
        tasks = await get_graph(db_session, graph_id)
        print(f"📦 Graph Tasks: {[t.agent_type for t in tasks]}")
        
        # Phase 2: Resume & Intercept
        print("\n[Phase 2] Resuming execution to trigger HITL intercept...")
        execution_events = []
        async for event in orch.resume(graph_id, "live-hitl-conv"):
            execution_events.append(event)
            print(f" -> Event: {event['event']}")
            
        approval_event = next((e for e in execution_events if e["event"] == "approval_required"), None)
        if not approval_event:
            print("❌ FAILURE: Orchestrator failed to halt for HITL approval!")
            return
            
        task_id = approval_event["data"]["id"]
        tool_name = approval_event["data"]["tool"]
        print(f"✅ Success: Intercepted tool '{tool_name}' for Task ID: {task_id}")
        
        # Phase 3: Developer Approval Integration
        print("\n[Phase 3] Injecting developer approval...")
        resume_events = []
        async for event in orch.resume_shell(task_id, True, "live-hitl-conv"):
            resume_events.append(event)
            print(f" -> Event: {event['event']}")
            
        complete_event = next((e for e in resume_events if e["event"] == "task_completed"), None)
        if not complete_event:
            print("❌ FAILURE: Orchestrator failed to finish execution path!")
            return
            
        print("✅ Success: Graph execution complete.")
        
        # Verify workspace side effect
        if test_file.exists():
            print(f"🎉 Success: Physical file {test_file} was created!")
            print(f"📄 Content:\n{test_file.read_text()}")
        else:
            print("❌ FAILURE: hello.py was not created in the workspace!")

if __name__ == "__main__":
    asyncio.run(run_live_test())
