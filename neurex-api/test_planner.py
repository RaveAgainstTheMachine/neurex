import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from core.agents.planner_agent import PlannerAgent
from core.context.manager import ContextManager
from core.context.rules_parser import RulesParser


async def main():
    rules = RulesParser()
    ctx = ContextManager()
    planner = PlannerAgent(rules, ctx)
    print("Testing PlannerAgent...")
    plan = []
    async for chunk in planner.plan("create a quick little sudoku game", "test_id"):
        if chunk["type"] == "result":
            plan = chunk["plan"]
            print("\nFINAL PLAN:", json.dumps(plan, indent=2))
        elif chunk["type"] == "token":
            print(chunk["text"], end="", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
