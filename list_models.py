import os
import sys
import json
import urllib.request

# Ensure we can import from the current directory
sys.path.append(os.getcwd())

# Load .env file manually
env_path = os.path.join(os.getcwd(), ".env")
if os.path.exists(env_path):
    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ[key.strip()] = value.strip()

API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    print("No API Key found.")
    sys.exit(1)

url = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"

try:
    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read().decode("utf-8"))
        print("Available Models:")
        for m in data.get("models", []):
            if "generateContent" in m.get("supportedGenerationMethods", []):
                print(f"- {m['name']}")
except Exception as e:
    print(f"Error listing models: {e}")
