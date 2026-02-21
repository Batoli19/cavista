import os
import threading
import time
import tempfile
import subprocess
from queue import Queue, Empty

import numpy as np
import sounddevice as sd
import scipy.io.wavfile as wav
import noisereduce as nr
import whisper
import pyttsx3
import tkinter as tk
from tkinter import ttk
import pandas as pd

# Optional: Speaker diarization
from pyannote.audio import Pipeline

# ==============================================================
# CONFIG
# ==============================================================
SAMPLE_RATE = 16000
CHANNELS = 1
FILENAME = "consultation.wav"

recording = False
audio_frames = []
start_time = None

# Whisper model for multilingual transcription
whisper_model = whisper.load_model("base")  # smaller or "medium" for better accuracy

# Load ICD-10 diseases CSV
# CSV format: disease_name,keywords (comma-separated, include Setswana + English)
diseases_df = pd.read_csv("icd10_diseases.csv")
diseases_df['keywords'] = diseases_df['keywords'].apply(lambda x: [k.strip().lower() for k in x.split(',')])

# Pyttsx3 TTS fallback
TTS_RATE = 180
TTS_VOLUME = 1.0
_tts_engine = pyttsx3.init()
_tts_engine.setProperty("rate", TTS_RATE)
_tts_engine.setProperty("volume", TTS_VOLUME)

# Edge TTS configuration
EDGE_TTS_ENABLED = True
EDGE_VOICE = "en-US-JennyNeural"
EDGE_RATE = "+0%"
EDGE_VOLUME = "+0%"

try:
    import edge_tts
except ImportError:
    EDGE_TTS_ENABLED = False

# Pyannote speaker diarization
diarization_pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization")

# ==============================================================
# UTILITY FUNCTIONS
# ==============================================================
def speak(text: str):
    text = text.strip()
    if not text:
        return
    if EDGE_TTS_ENABLED:
        # Generate mp3 and play
        out_path = os.path.join(tempfile.gettempdir(), "tts_output.mp3")
        async def _run_edge():
            communicate = edge_tts.Communicate(text=text, voice=EDGE_VOICE, rate=EDGE_RATE, volume=EDGE_VOLUME)
            await communicate.save(out_path)
        import asyncio
        asyncio.run(_run_edge())
        subprocess.Popen(["cmd", "/c", "start", "/min", "", out_path], shell=True)
    else:
        _tts_engine.say(text)
        _tts_engine.runAndWait()

# ==============================================================
# ADVANCED DIAGNOSIS ENGINE
# ==============================================================
def diagnose_advanced(text: str):
    text = text.lower()
    matched_diseases = []

    for _, row in diseases_df.iterrows():
        for kw in row['keywords']:
            if kw in text:
                matched_diseases.append(row['disease_name'])
                break

    if not matched_diseases:
        return "No clear diagnosis detected. Recommend further medical evaluation."

    severity_order = [
        "Heart attack", "Stroke", "Cancer", "Brain tumor", "Pulmonary embolism",
        "Sepsis", "Kidney failure", "Diabetes"
    ]

    sorted_diseases = sorted(
        matched_diseases,
        key=lambda x: severity_order.index(x) if x in severity_order else len(severity_order) + 1
    )

    return ", ".join(sorted_diseases)

# ==============================================================
# AUDIO RECORDING
# ==============================================================
def record_audio():
    global recording, audio_frames
    def callback(indata, frames, time_info, status):
        if recording:
            audio_frames.append(indata.copy())
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, callback=callback):
        while recording:
            sd.sleep(100)

def start_recording():
    global recording, audio_frames, start_time
    recording = True
    audio_frames = []
    start_time = time.time()
    indicator_label.config(text="🟢 Listening", foreground="green")
    threading.Thread(target=record_audio, daemon=True).start()
    update_timer()

def stop_recording():
    global recording
    recording = False
    indicator_label.config(text="🔴 Stopped", foreground="red")
    save_audio()

# ==============================================================
# SAVE AUDIO + NOISE REDUCTION
# ==============================================================
def save_audio():
    global audio_frames
    if not audio_frames:
        return
    audio = np.concatenate(audio_frames, axis=0)
    reduced = nr.reduce_noise(y=audio.flatten(), sr=SAMPLE_RATE)
    wav.write(FILENAME, SAMPLE_RATE, reduced)
    process_audio(FILENAME)

# ==============================================================
# PROCESS AUDIO: DIARIZATION + TRANSCRIPTION + DIAGNOSIS
# ==============================================================
def process_audio(file_path):
    # Speaker diarization
    diarization = diarization_pipeline(file_path)
    segments = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        segments.append((turn.start, turn.end, speaker))

    full_transcript = ""
    patient_transcript = ""

    for start, end, speaker in segments:
        # Extract audio segment
        start_sample = int(start * SAMPLE_RATE)
        end_sample = int(end * SAMPLE_RATE)
        segment_audio = np.concatenate(audio_frames, axis=0)[start_sample:end_sample]

        # Save temp segment file
        temp_path = os.path.join(tempfile.gettempdir(), f"seg_{speaker}.wav")
        wav.write(temp_path, SAMPLE_RATE, segment_audio)

        # Transcribe with Whisper
        result = whisper_model.transcribe(temp_path)
        text = result['text']
        full_transcript += f"[{speaker}] {text}\n"

        # Assume patient = main speaker
        if "SPEAKER_0" in speaker:  # Customize depending on diarization
            patient_transcript += text + " "

    transcript_box.delete("1.0", tk.END)
    transcript_box.insert(tk.END, full_transcript)

    # Diagnose only patient speech
    diagnosis_text = diagnose_advanced(patient_transcript)
    diagnosis_box.delete("1.0", tk.END)
    diagnosis_box.insert(tk.END, diagnosis_text)

    # Speak diagnosis
    speak(diagnosis_text)

# ==============================================================
# TIMER
# ==============================================================
def update_timer():
    if recording:
        elapsed = int(time.time() - start_time)
        mins = elapsed // 60
        secs = elapsed % 60
        timer_label.config(text=f"{mins:02d}:{secs:02d}")
        root.after(1000, update_timer)

# ==============================================================
# GUI
# ==============================================================
root = tk.Tk()
root.title("Advanced Multilingual Clinical Voice Assistant")
root.geometry("800x600")

title = ttk.Label(root, text="Multilingual Clinical Consultation System", font=("Arial", 16))
title.pack(pady=10)

indicator_label = ttk.Label(root, text="🔴 Idle", font=("Arial", 12))
indicator_label.pack()

timer_label = ttk.Label(root, text="00:00", font=("Arial", 18))
timer_label.pack(pady=5)

start_btn = ttk.Button(root, text="Start Consultation", command=start_recording)
start_btn.pack(pady=5)

stop_btn = ttk.Button(root, text="Stop Consultation", command=stop_recording)
stop_btn.pack(pady=5)

ttk.Label(root, text="Transcript").pack()
transcript_box = tk.Text(root, height=12)
transcript_box.pack()

ttk.Label(root, text="AI Preliminary Diagnosis").pack()
diagnosis_box = tk.Text(root, height=8)
diagnosis_box.pack()

root.mainloop()
