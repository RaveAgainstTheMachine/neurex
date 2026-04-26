import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

WORKSPACE_PATH = os.getenv("WORKSPACE_PATH", "/workspace")
SKILLS_DIR = Path(WORKSPACE_PATH) / ".neurex" / "skills"

print(f"WORKSPACE_PATH: {WORKSPACE_PATH}")
print(f"SKILLS_DIR: {SKILLS_DIR}")
print(f"Exists: {SKILLS_DIR.exists()}")

if SKILLS_DIR.exists():
    print(f"Contents: {os.listdir(SKILLS_DIR)}")
