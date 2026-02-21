import os
import re
import threading
import tempfile
import subprocess
import asyncio
from queue import Queue, Empty
from typing import Optional

import pyttsx3
import speech_recognition as sr

# ============================================================
# CONFIG
# ============================================================

# --- STT ---
STT_TIMEOUT = 5
STT_PHRASE_TIME_LIMIT = 7

# --- pyttsx3 fallback ---
TTS_RATE = 180
TTS_VOLUME = 1.0

# --- Edge TTS (primary) ---
EDGE_TTS_ENABLED = os.environ.get("EDGE_TTS_ENABLED", "1").lower() in ("1", "true", "yes", "on")
EDGE_VOICE = os.environ.get("TTS_VOICE", "en-US-JennyNeural")
EDGE_RATE = os.environ.get("TTS_RATE", "+0%")       # "+10%" or "-10%"
EDGE_VOLUME = os.environ.get("TTS_VOLUME", "+0%")   # "+20%"


# ============================================================
# HELPERS
# ============================================================

def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()

def _split_sentences(text: str) -> list[str]:
    """
    Split into natural chunks but keep them reasonably short.
    """
    text = _clean_text(text)
    if not text:
        return []
    parts = re.split(r"(?<=[.!?])\s+", text)
    parts = [p.strip() for p in parts if p.strip()]
    return parts if parts else [text]


# ============================================================
# EDGE TTS (PRIMARY) - WORKER THREAD
# ============================================================

def _try_import_edge_tts():
    try:
        import edge_tts  # type: ignore
        return edge_tts
    except Exception:
        return None

_edge_tts_mod = _try_import_edge_tts()

class _EdgeTTSWorker:
    """
    Owns Edge-TTS generation in one background thread.
    Generates an mp3 and plays it using Windows 'start'.
    Falls back to pyttsx3 if edge-tts is missing or fails.
    """
    def __init__(self) -> None:
        self._q: "Queue[str]" = Queue()
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _play_mp3_windows(self, path: str) -> None:
        # Uses Windows built-in "start" to open default audio player
        # /min keeps it from stealing focus too much
        subprocess.Popen(["cmd", "/c", "start", "/min", "", path], shell=True)

    def _generate_and_play(self, text: str) -> bool:
        """
        Returns True if Edge-TTS succeeded, False otherwise.
        """
        if not EDGE_TTS_ENABLED:
            return False
        if _edge_tts_mod is None:
            return False

        text = _clean_text(text)
        if not text:
            return True

        # Keep file name constant to avoid temp-folder spam
        out_path = os.path.join(tempfile.gettempdir(), "jarvis_tts.mp3")

        async def _run_async():
            communicate = _edge_tts_mod.Communicate(
                text=text,
                voice=EDGE_VOICE,
                rate=EDGE_RATE,
                volume=EDGE_VOLUME
            )
            await communicate.save(out_path)

        try:
            # Run async generation safely in this thread
            asyncio.run(_run_async())
            self._play_mp3_windows(out_path)
            return True
        except RuntimeError:
            # If an event loop exists (rare), create a new loop
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(_run_async())
                loop.close()
                self._play_mp3_windows(out_path)
                return True
            except Exception:
                return False
        except Exception:
            return False

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                text = self._q.get(timeout=0.1)
            except Empty:
                continue

            # Drain queue: keep only latest (prevents backlog)
            latest = text
            while True:
                try:
                    latest = self._q.get_nowait()
                except Empty:
                    break

            latest = _clean_text(latest)
            if not latest:
                continue

            ok = self._generate_and_play(latest)
            if not ok:
                # Edge failed → fallback to pyttsx3
                _tts.speak(latest)

    def speak(self, text: str) -> None:
        text = _clean_text(text)
        if not text:
            return
        self._q.put(text)

    def shutdown(self) -> None:
        self._stop_event.set()


# ============================================================
# pyttsx3 FALLBACK - SINGLE OWNER WORKER THREAD
# ============================================================

class _TTSWorker:
    """
    Owns the pyttsx3 engine in exactly one thread.
    This avoids pyttsx3/SAPI issues where only the first word is spoken.
    """
    def __init__(self, rate: int = TTS_RATE, volume: float = TTS_VOLUME) -> None:
        self._engine = pyttsx3.init()
        self._engine.setProperty("rate", rate)
        self._engine.setProperty("volume", volume)

        self._q: "Queue[str]" = Queue()
        self._stop_event = threading.Event()

        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                text = self._q.get(timeout=0.1)
            except Empty:
                continue

            # Drain queue: keep only latest
            latest = text
            while True:
                try:
                    latest = self._q.get_nowait()
                except Empty:
                    break

            latest = _clean_text(latest)
            if not latest:
                continue

            try:
                self._engine.stop()
                for chunk in _split_sentences(latest):
                    self._engine.say(chunk)
                self._engine.runAndWait()
            except Exception:
                try:
                    self._engine.stop()
                except Exception:
                    pass

    def speak(self, text: str) -> None:
        text = _clean_text(text)
        if not text:
            return
        self._q.put(text)

    def shutdown(self) -> None:
        self._stop_event.set()
        try:
            self._engine.stop()
        except Exception:
            pass


# Instantiate workers
_tts = _TTSWorker()
_edge_tts = _EdgeTTSWorker()


def speak(text: str) -> None:
    """
    Non-blocking speak.
    Uses Edge-TTS if available/enabled, otherwise falls back to pyttsx3.
    """
    text = _clean_text(text)
    if not text:
        return

    # Prefer Edge TTS (neural, more human)
    if EDGE_TTS_ENABLED and _edge_tts_mod is not None:
        _edge_tts.speak(text)
    else:
        _tts.speak(text)


# ============================================================
# STT: SPEECH TO TEXT
# ============================================================

_recognizer = sr.Recognizer()

def listen_command(timeout: int = STT_TIMEOUT, phrase_time_limit: int = STT_PHRASE_TIME_LIMIT) -> str:
    """
    Push-to-talk listen once.
    Returns recognized text OR 'VOICE_ERROR: ...' (never raises).
    """
    try:
        with sr.Microphone() as source:
            _recognizer.adjust_for_ambient_noise(source, duration=1)
            audio = _recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)

        text = _recognizer.recognize_google(audio)
        text = _clean_text(text)
        if not text:
            return "VOICE_ERROR: Empty speech"
        return text

    except sr.WaitTimeoutError:
        return "VOICE_ERROR: Timeout (no speech detected)"
    except sr.UnknownValueError:
        return "VOICE_ERROR: Could not understand speech"
    except sr.RequestError:
        return "VOICE_ERROR: Speech recognition service unavailable"
    except Exception as e:
        return f"VOICE_ERROR: {str(e)}"


# ============================================================
# OPTIONAL: quick local test (won't run unless you run this file)
# ============================================================

if __name__ == "__main__":
    print("EDGE_TTS_ENABLED:", EDGE_TTS_ENABLED)
    print("EDGE_TTS_AVAILABLE:", _edge_tts_mod is not None)
    speak("Alright. I created the project. Want me to generate a plan next?")
    cmd = listen_command()
    print(cmd)
