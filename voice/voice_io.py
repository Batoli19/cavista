import re
import threading
from queue import Queue, Empty
from typing import Optional

import pyttsx3
import speech_recognition as sr

# ============================================================
# CONFIG
# ============================================================

TTS_RATE = 180
TTS_VOLUME = 1.0

STT_TIMEOUT = 5
STT_PHRASE_TIME_LIMIT = 7


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
# TTS: SINGLE-OWNER WORKER THREAD (FIXES "ONLY SAYS ALRIGHT")
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

        # Start worker thread
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                text = self._q.get(timeout=0.1)
            except Empty:
                continue

            # Drain queue: keep only the latest message (prevents backlog)
            latest = text
            while True:
                try:
                    latest = self._q.get_nowait()
                except Empty:
                    break

            latest = _clean_text(latest)
            if not latest:
                continue

            # Speak (single thread owns engine)
            try:
                self._engine.stop()  # cancel anything currently speaking
                for chunk in _split_sentences(latest):
                    self._engine.say(chunk)
                self._engine.runAndWait()
            except Exception:
                # Never crash app because TTS failed
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


_tts = _TTSWorker()


def speak(text: str) -> None:
    """
    Non-blocking. Safe to call from UI.
    Always speaks the FULL text (no 'only says alright' bug).
    """
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
            # Calibrate for ambient noise
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
    speak("Alright. I created the project. Want me to generate a plan next?")
    cmd = listen_command()
    print(cmd)
