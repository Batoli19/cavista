"""
JARVIS Local Server v3.0
=========================
    python jarvis_server.py
Then open http://localhost:7878 in Chrome.
"""

import os, sys, json, time, threading, subprocess, webbrowser, re, traceback
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

try:
    from groq import Groq
except ImportError:
    sys.exit("[ERROR] Run: pip install groq")

try:
    import pyautogui
    pyautogui.FAILSAFE = False   # don't abort on corner mouse
    pyautogui.PAUSE = 0.3
except ImportError:
    sys.exit("[ERROR] Run: pip install pyautogui")

try:
    import pyttsx3
    HAS_TTS = True
except ImportError:
    HAS_TTS = False
    print("[WARN] pyttsx3 missing — no voice. Run: pip install pyttsx3")

# ══════════════════════════════════════════════════════════════════════════════
#  ↓↓  PASTE YOUR GROQ KEY HERE  ↓↓
# ══════════════════════════════════════════════════════════════════════════════
Api_KEY = "not pasted cause of github restrictions and stuff"
# ══════════════════════════════════════════════════════════════════════════════

PORT    = 7878
UI_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jarvis_ui.html")

APPS = {
    "notepad"     : "notepad.exe",
    "word"        : r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
    "excel"       : r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
    "chrome"      : r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "firefox"     : r"C:\Program Files\Mozilla Firefox\firefox.exe",
    "vscode"      : r"C:\Users\user\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "calculator"  : "calc.exe",
    "paint"       : "mspaint.exe",
    "explorer"    : "explorer.exe",
    "cmd"         : "cmd.exe",
    "powershell"  : "powershell.exe",
    "spotify"     : r"C:\Users\user\AppData\Roaming\Spotify\Spotify.exe",
    "task manager": "taskmgr.exe",
}

# ── System prompt — very explicit so AI always uses action tags ───────────────
SYSTEM = """You are JARVIS, Iron Man's AI assistant. You control a real Windows PC.

CRITICAL RULE: When the user asks you to DO something on the PC, you MUST include an <action> tag.
Never just SAY you did something — actually trigger the action.

Format:
<action>{"type": "ACTION_TYPE", "param": "value"}</action>

ACTION TYPES (use EXACTLY these):
- open_app       → <action>{"type": "open_app", "app": "chrome"}</action>
- screenshot     → <action>{"type": "screenshot"}</action>
- search_google  → <action>{"type": "search_google", "query": "cats"}</action>
- search_youtube → <action>{"type": "search_youtube", "query": "lofi music"}</action>
- open_url       → <action>{"type": "open_url", "url": "https://github.com"}</action>
- run_cmd        → <action>{"type": "run_cmd", "command": "ipconfig"}</action>
- type_text      → <action>{"type": "type_text", "text": "hello world"}</action>
- volume_up      → <action>{"type": "volume_up"}</action>
- volume_down    → <action>{"type": "volume_down"}</action>
- mute           → <action>{"type": "mute"}</action>
- close_window   → <action>{"type": "close_window"}</action>
- minimize       → <action>{"type": "minimize"}</action>
- maximize       → <action>{"type": "maximize"}</action>
- save           → <action>{"type": "save"}</action>
- get_time       → <action>{"type": "get_time"}</action>

APP NAMES: chrome, word, excel, notepad, vscode, calculator, paint, explorer, cmd, powershell, spotify

EXAMPLES (follow these exactly):
User: "take a screenshot" → "On it, sir.<action>{"type": "screenshot"}</action>"
User: "open chrome" → "Opening Chrome now.<action>{"type": "open_app", "app": "chrome"}</action>"
User: "search youtube for lofi" → "Searching YouTube.<action>{"type": "search_youtube", "query": "lofi"}</action>"
User: "open notepad" → "Notepad coming right up.<action>{"type": "open_app", "app": "notepad"}</action>"

PERSONALITY: Sharp, witty, efficient, slightly sarcastic like Tony Stark's AI.
Keep text replies SHORT (1-3 sentences). They are read aloud."""


# ══════════════════════════════════════════════════════════════════════════════
#  VOICE  (threaded — never blocks)
# ══════════════════════════════════════════════════════════════════════════════
class Voice:
    def __init__(self):
        self._q    = []
        self._lock = threading.Lock()
        self._busy = threading.Event()
        self.on    = HAS_TTS
        if self.on:
            threading.Thread(target=self._worker, daemon=True).start()
            print("  🔊  Voice output enabled.")
        else:
            print("  🔇  Voice disabled (pip install pyttsx3 to enable).")

    def _make_engine(self):
        e = pyttsx3.init()
        voices = e.getProperty("voices")
        # Use voice index 2 (Zira) if available
        if voices and len(voices) > 2:
            e.setProperty("voice", voices[2].id)
        elif voices:
            e.setProperty("voice", voices[0].id)
        e.setProperty("rate", 180)
        e.setProperty("volume", 1.0)
        return e

    def _worker(self):
        engine = self._make_engine()
        while True:
            with self._lock:
                text = self._q.pop(0) if self._q else None
            if text:
                self._busy.set()
                try:
                    engine.say(text)
                    engine.runAndWait()
                except Exception:
                    try: engine.stop()
                    except: pass
                    engine = self._make_engine()
                finally:
                    self._busy.clear()
            else:
                time.sleep(0.04)

    def say(self, text: str):
        """Queue text to be spoken aloud (non-blocking)."""
        if not self.on or not text.strip():
            return
        # Clean up text for speaking — remove any leftover tags
        clean = re.sub(r'<[^>]+>', '', text).strip()
        if clean:
            with self._lock:
                self._q.append(clean)
            print(f"  🔊  Speaking: {clean[:60]}{'...' if len(clean)>60 else ''}")


# ══════════════════════════════════════════════════════════════════════════════
#  PC CONTROLLER  (with debug printing so you can see what runs)
# ══════════════════════════════════════════════════════════════════════════════
class PC:
    def open(self, name: str) -> str:
        key  = name.lower().strip()
        path = APPS.get(key)
        if not path:
            for k, v in APPS.items():
                if k in key or key in k:
                    path = v; key = k; break
        path = path or name
        print(f"  [PC] Opening: {key} → {path}")
        try:
            subprocess.Popen(str(path), shell=True)
            return f"Opened {key}."
        except Exception as e:
            print(f"  [PC] Error opening {key}: {e}")
            return f"Failed to open {key}."

    def screenshot(self) -> str:
        desk = os.path.join(os.path.expanduser("~"), "Desktop")
        fn   = f"JARVIS_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        path = os.path.join(desk, fn)
        print(f"  [PC] Screenshot → {path}")
        try:
            img = pyautogui.screenshot()
            img.save(path)
            return f"Screenshot saved to Desktop as {fn}."
        except Exception as e:
            print(f"  [PC] Screenshot error: {e}")
            return "Screenshot failed."

    def search_google(self, q: str) -> str:
        url = f"https://www.google.com/search?q={q.replace(' ', '+')}"
        print(f"  [PC] Google: {q}")
        webbrowser.open(url)
        return f"Searching Google for {q}."

    def search_youtube(self, q: str) -> str:
        url = f"https://www.youtube.com/results?search_query={q.replace(' ', '+')}"
        print(f"  [PC] YouTube: {q}")
        webbrowser.open(url)
        return f"Searching YouTube for {q}."

    def open_url(self, url: str) -> str:
        if not url.startswith("http"): url = "https://" + url
        print(f"  [PC] URL: {url}")
        webbrowser.open(url)
        return f"Opened {url}."

    def run_cmd(self, command: str) -> str:
        print(f"  [PC] CMD: {command}")
        subprocess.Popen(f'start cmd /k "{command}"', shell=True)
        return f"Running: {command}"

    def type_text(self, text: str) -> str:
        print(f"  [PC] Typing: {text[:40]}")
        try:
            import tkinter as tk
            r = tk.Tk(); r.withdraw()
            r.clipboard_clear(); r.clipboard_append(text); r.update()
            time.sleep(0.4)
            pyautogui.hotkey("ctrl", "v")
            r.destroy()
            return "Text typed."
        except Exception as e:
            print(f"  [PC] Type error: {e}")
            return "Typing failed."

    def volume(self, direction: str) -> str:
        key = "volumeup" if direction == "up" else "volumedown"
        print(f"  [PC] Volume {direction}")
        pyautogui.press(key, presses=5)
        return f"Volume {direction}."

    def mute(self)         -> str: pyautogui.press("volumemute"); return "Muted."
    def close_window(self) -> str: pyautogui.hotkey("alt","f4"); return "Window closed."
    def minimize(self)     -> str: pyautogui.hotkey("win","down"); return "Minimized."
    def maximize(self)     -> str: pyautogui.hotkey("win","up"); return "Maximized."
    def save(self)         -> str: pyautogui.hotkey("ctrl","s"); return "Saved."
    def time_now(self)     -> str:
        n = datetime.now()
        return f"It's {n.strftime('%I:%M %p')}, {n.strftime('%A, %B %d')}."


# ══════════════════════════════════════════════════════════════════════════════
#  BRAIN
# ══════════════════════════════════════════════════════════════════════════════
class Brain:
    def __init__(self, pc: PC, voice: Voice):
        self.pc      = pc
        self.voice   = voice
        self.history = []
        key = API_KEY or os.getenv("GROQ_API_KEY", "")
        if not key:
            sys.exit("\n  ❌  No API key! Set API_KEY in jarvis_server.py\n")
        self.client = Groq(api_key=key)
        print("  ✅  Groq AI connected.")

    def respond(self, user_msg: str) -> str:
        self.history.append({"role": "user", "content": user_msg})

        try:
            r = self.client.chat.completions.create(
                model    = "llama-3.3-70b-versatile",
                max_tokens = 400,
                temperature = 0.7,
                messages = [{"role": "system", "content": SYSTEM}] + self.history[-20:]
            )
            raw = r.choices[0].message.content.strip()
        except Exception as e:
            raw = f"Brain error: {e}"

        print(f"\n  🤖 Raw response: {raw[:120]}")
        self.history.append({"role": "assistant", "content": raw})

        # ── Execute all <action> tags ─────────────────────────────────────
        pattern = re.compile(r'<action>\s*(.*?)\s*</action>', re.DOTALL | re.IGNORECASE)
        action_results = []

        for act_raw in pattern.findall(raw):
            print(f"  ⚙  Action found: {act_raw.strip()}")
            try:
                d = json.loads(act_raw.strip())
                t = d.get("type", "")
                result = "done"

                if   t == "open_app"      : result = self.pc.open(d.get("app", ""))
                elif t == "screenshot"    : result = self.pc.screenshot()
                elif t == "search_google" : result = self.pc.search_google(d.get("query", ""))
                elif t == "search_youtube": result = self.pc.search_youtube(d.get("query", ""))
                elif t == "open_url"      : result = self.pc.open_url(d.get("url", ""))
                elif t == "run_cmd"       : result = self.pc.run_cmd(d.get("command", ""))
                elif t == "type_text"     : result = self.pc.type_text(d.get("text", ""))
                elif t == "volume_up"     : result = self.pc.volume("up")
                elif t == "volume_down"   : result = self.pc.volume("down")
                elif t == "mute"          : result = self.pc.mute()
                elif t == "close_window"  : result = self.pc.close_window()
                elif t == "minimize"      : result = self.pc.minimize()
                elif t == "maximize"      : result = self.pc.maximize()
                elif t == "save"          : result = self.pc.save()
                elif t == "get_time"      : result = self.pc.time_now()
                else:
                    print(f"  ⚠  Unknown action type: {t}")

                print(f"  ✅  Action result: {result}")
                action_results.append(result)

            except json.JSONDecodeError as e:
                print(f"  ❌  JSON parse error: {e} — raw: {act_raw}")
            except Exception as e:
                print(f"  ❌  Action error: {e}")
                traceback.print_exc()

        # ── Clean spoken text (strip action tags) ─────────────────────────
        spoken = pattern.sub("", raw).strip()

        # If get_time was called, use that as the response
        for res in action_results:
            if "It's" in str(res):
                spoken = res

        if not spoken:
            spoken = "Done, sir."

        # ── Speak it aloud ────────────────────────────────────────────────
        self.voice.say(spoken)

        return spoken


# ══════════════════════════════════════════════════════════════════════════════
#  HTTP HANDLER
# ══════════════════════════════════════════════════════════════════════════════
_brain = None

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a): pass  # silence HTTP logs

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors(); self.end_headers()

    def do_GET(self):
        if self.path in ("/", "/index.html", "/jarvis_ui.html"):
            if os.path.exists(UI_FILE):
                data = open(UI_FILE, "rb").read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self._cors(); self.end_headers()
                self.wfile.write(data)
            else:
                self._text(f"UI not found: {UI_FILE}", 404)
        elif self.path == "/ping":
            self._json({"status": "online", "model": "llama-3.3-70b-versatile (Groq)"})
        else:
            self._text("Not found", 404)

    def do_POST(self):
        if self.path == "/chat":
            try:
                n    = int(self.headers.get("Content-Length", 0))
                data = json.loads(self.rfile.read(n))
                msg  = data.get("message", "").strip()
                if not msg:
                    self._json({"error": "empty message"}, 400); return
                print(f"\n  💬 User: {msg}")
                reply = _brain.respond(msg)
                print(f"  📤  Sending to UI: {reply[:80]}")
                self._json({"reply": reply})
            except Exception as e:
                traceback.print_exc()
                self._json({"error": str(e)}, 500)
        else:
            self._text("Not found", 404)

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin",  "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json(self, d, code=200):
        b = json.dumps(d).encode()
        self.send_response(code)
        self._cors()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers(); self.wfile.write(b)

    def _text(self, t, code=200):
        b = t.encode()
        self.send_response(code)
        self._cors()
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers(); self.wfile.write(b)


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("""
  ╔══════════════════════════════════════════╗
  ║   J·A·R·V·I·S  Server  v3.0             ║
  ║   Groq AI  |  Voice  |  PC Control      ║
  ╚══════════════════════════════════════════╝""")

    voice  = Voice()
    pc     = PC()
    _brain = Brain(pc, voice)

    server = HTTPServer(("localhost", PORT), Handler)
    print(f"\n  👉  Open Chrome: http://localhost:{PORT}")
    print(f"  📂  UI file: {UI_FILE}")
    print(f"  Press Ctrl+C to stop.\n")
    print("  " + "─" * 44)

    voice.say("JARVIS online. All systems ready, sir.")

    def _open_browser():
        time.sleep(1.5)
        webbrowser.open(f"http://localhost:{PORT}")
    threading.Thread(target=_open_browser, daemon=True).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Shutting down.")
        voice.say("Goodbye, sir.")
        time.sleep(1.2)