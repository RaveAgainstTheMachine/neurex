import asyncio
import os
from core.agents.planner_agent import PlannerAgent
from core.context.manager import ContextManager
from core.context.rules_parser import RulesParser
from dotenv import load_dotenv

async def test_planner():
    load_dotenv("../.env")
    rules = RulesParser()
    ctx = ContextManager()
    planner = PlannerAgent(rules, ctx)
    
    print("Asking Planner to think...")
    async for chunk in planner.plan("Implement shell approval", "test-conv"):
        if chunk["type"] == "token":
            print(chunk["text"], end="", flush=True)
        elif chunk["type"] == "result":
            print("\nPlan received!")
            import json
            print(json.dumps(chunk["plan"], indent=2))

if __name__ == "__main__":
    asyncio.run(test_planner())
