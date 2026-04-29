import requests

API_BASE = "http://localhost:8000"
TOKEN = "YOUR_TOKEN_HERE" # I'll need to find a way to get a token or just test without auth if possible

# Try to get settings first
res = requests.get(f"{API_BASE}/api/settings/")
print("GET settings:", res.json())

# Try to update
payload = {
    "settings": {
        "accent_color": "#ff0000",
        "glow_color": "#ff000066"
    }
}
res = requests.post(f"{API_BASE}/api/settings/", json=payload)
print("POST settings status:", res.status_code)
print("POST settings response:", res.json())

# Check if persisted
res = requests.get(f"{API_BASE}/api/settings/")
print("GET settings again:", res.json())
