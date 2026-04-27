
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from core.orchestrator import Orchestrator
from core.context.manager import ContextManager
from core.context.rules_parser import RulesParser

async def trigger():
    # Dynamically determine workspace path
    os.environ["WORKSPACE_PATH"] = os.getenv("WORKSPACE_PATH", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.environ["CHROMA_DB_DIR"] = "/games/AI/chroma_db"
    
    DATABASE_URL = "sqlite+aiosqlite:///./neurex.db"
    engine = create_async_engine(DATABASE_URL)
    
    # Init deps
    rules = RulesParser() 
    ctx_manager = ContextManager() 
    
    async with AsyncSession(engine) as session:
        orchestrator = Orchestrator(session, rules, ctx_manager)
        conversation_id = "default"
        message = "Implement a Human-in-the-loop Shell Approval workflow. Update terminal.py to detect unsafe commands and the UI to show an Approve/Deny button."
        
        print(f"Force-triggering task...")
        
        async for event in orchestrator.run(message, conversation_id):
            if event.get("event") == "plan_ready":
                print("\nPLAN READY!")
                break
            elif event.get("event") == "token":
                print(event["data"], end="", flush=True)
        
        print("\nTrigger complete.")

if __name__ == "__main__":
    asyncio.run(trigger())
