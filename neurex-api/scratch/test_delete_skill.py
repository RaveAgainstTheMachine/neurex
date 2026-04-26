import requests
import os

API_BASE = "http://127.0.0.1:8000"
TOKEN = os.getenv("NEUREX_ADMIN_TOKEN", "default_admin_token") # I'll assume standard token or check auth.py

def test_delete():
    # 1. List skills
    resp = requests.get(f"{API_BASE}/api/infra/skills")
    skills = resp.json()
    print(f"Skills: {skills}")
    
    if not skills:
        print("No skills to delete")
        return
        
    skill_id = skills[0]['id']
    print(f"Attempting to delete: {skill_id}")
    
    # 2. Delete
    headers = {"Authorization": f"Bearer {TOKEN}"}
    resp = requests.delete(f"{API_BASE}/api/infra/skills/{skill_id}", headers=headers)
    print(f"Response: {resp.status_code} - {resp.text}")

if __name__ == "__main__":
    test_delete()
