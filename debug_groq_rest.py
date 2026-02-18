import os
import sys
import json
import urllib.request
import urllib.error

# Ensure we can import from the current directory
sys.path.append(os.getcwd())

# Load .env file manually
env_path = os.path.join(os.getcwd(), ".env")
if os.path.exists(env_path):
    print(f"[Debug] Loading environment from {env_path}")
    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ[key.strip()] = value.strip()

API_KEY = os.environ.get("GROQ_API_KEY")
MODEL = os.environ.get("GROQ_MODEL_NAME", "llama-3.3-70b-versatile")

print(f"Groq Key Present: {bool(API_KEY)}")
print(f"Groq Model: {MODEL}")

if not API_KEY:
    print("Error: Missing GROQ_API_KEY")
    sys.exit(1)

def chat_with_groq(message):
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": message}
        ],
        "temperature": 0.7
    }
    
    data = json.dumps(payload).encode("utf-8")
    
    req = urllib.request.Request(
        url, 
        data=data, 
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            resp_body = response.read().decode("utf-8")
            resp_data = json.loads(resp_body)
            return resp_data["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code}")
        print(e.read().decode("utf-8"))
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

print("Testing Groq...")
response = chat_with_groq("Hello, say 'Groq is working' if you can hear me.")
print(f"Response: {response}")
