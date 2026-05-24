import sys
import os
import asyncio

# Add neurex-api path to sys.path so we can import core modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../neurex-api")))

from core.security.sentinel import SecuritySentinel

async def main():
    # Detect the workspace path
    workspace_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    print(f"🔍 Running Security Sentinel Audit on workspace: {workspace_path}")
    
    sentinel = SecuritySentinel(workspace_path)
    report = await sentinel.audit_workspace()
    
    issues = report.get("issues", {})
    if not issues:
        print("✅ No security violations found by Security Sentinel!")
    else:
        print(f"❌ Found {len(issues)} vulnerable file(s):")
        for file, file_issues in issues.items():
            print(f"\n📁 File: {file}")
            for issue in file_issues:
                print(f"   [{issue['severity']}] Line {issue['line']}: {issue['message']}")

if __name__ == "__main__":
    asyncio.run(main())
