import http.server
import socketserver
import json
import os
import sys

# Ensure we can import from the current directory
# Ensure we can import from the current directory
sys.path.append(os.getcwd())

# Load .env file manually to avoid 'python-dotenv' dependency
env_path = os.path.join(os.getcwd(), ".env")
if os.path.exists(env_path):
    print(f"[Server] Loading environment from {env_path}")
    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ[key.strip()] = value.strip()
else:
    print("[Server] No .env file found. AI features may be disabled.")

# Import the existing command handler from main.py
try:
    from main import handle_command
except ImportError:
    print("Error: Could not import handle_command from main.py")
    def handle_command(cmd, files=None): return f"Error: Backend connection failed. Command: {cmd}"

PORT = 8000
DIRECTORY = "ui"

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Serve files from the 'ui' directory
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_POST(self):
        if self.path == "/api/command":
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                command = data.get("command", "")
                files = data.get("files", [])
                
                print(f"[Server] Received command: {command} | Files: {len(files)}")
                
                # Call the actual engine logic
                reply = handle_command(command, files)
                print(f"[Server] Reply: {reply}")
                
                response = {"reply": reply}
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
            except Exception as e:
                print(f"[Server] Error: {e}")
                self.send_error(500, str(e))
        else:
            self.send_error(404)

print(f"Starting Jarvis Web Server at http://localhost:{PORT}")
print("Press Ctrl+C to stop.")

# Allow address reuse to prevent "Address already in use" errors on restart
socketserver.TCPServer.allow_reuse_address = True

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.shutdown()
