import os
import threading
import time
import tempfile
import subprocess
import logging
from queue import Queue

import numpy as np
import sounddevice as sd
import scipy.io.wavfile as wav
import noisereduce as nr
import whisper
import pyttsx3
import tkinter as tk
from tkinter import ttk
import pandas as pd
from pyannote.audio import Pipeline

# ==============================================================
# LOGGING SYSTEM (NEW)
# ==============================================================
logging.basicConfig(
    filename="system.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ==============================================================
# CONFIG
# ==============================================================
SAMPLE_RATE = 16000
CHANNELS = 1
FILENAME = "consultation.wav"

recording = False
audio_frames = []
start_time = None

# Whisper model (dynamic selection ready)
MODEL_NAME = "base"
whisper_model = whisper.load_model(MODEL_NAME)

# Load ICD-10 CSV
diseases_df = pd.read_csv("icd10_diseases.csv")
diseases_df['keywords'] = diseases_df['keywords'].apply(
    lambda x: [k.strip().lower() for k in x.split(',')]
)

# TTS
_tts_engine = pyttsx3.init()
_tts_engine.setProperty("rate", 180)
_tts_engine.setProperty("volume", 1.0)

# Speaker diarization
try:
    diarization_pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization")
except Exception as e:
    logging.error(f"Diarization model failed: {e}")
    diarization_pipeline = None

# ==============================================================
# SPEAK FUNCTION
# ==============================================================
def speak(text: str):
    try:
        _tts_engine.say(text)
        _tts_engine.runAndWait()
    except Exception as e:
        logging.error(f"TTS error: {e}")

# ==============================================================
# RISK CLASSIFICATION (NEW)
# ==============================================================
def risk_level(diseases):
    critical = ["Heart attack", "Stroke", "Sepsis"]
    for d in critical:
        if d in diseases:
            return "CRITICAL"
    return "MODERATE"

# ==============================================================
# ADVANCED DIAGNOSIS ENGINE (Enhanced)
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
        "Heart attack", "Stroke", "Cancer", "Brain tumor",
        "Pulmonary embolism", "Sepsis", "Kidney failure", "Diabetes"
    ]

    sorted_diseases = sorted(
        matched_diseases,
        key=lambda x: severity_order.index(x) if x in severity_order else len(severity_order)
    )

    confidence = min(len(sorted_diseases) * 30, 100)
    risk = risk_level(sorted_diseases)

    return f"Possible Conditions: {', '.join(sorted_diseases)}\nConfidence: {confidence}%\nRisk Level: {risk}"

# ==============================================================
# RECORDING
# ==============================================================
def record_audio():
    global recording, audio_frames

    def callback(indata, frames, time_info, status):
        if recording:
            audio_frames.append(indata.copy())
            volume = int(np.linalg.norm(indata) * 10)
            audio_level_label.config(text=f"Audio Level: {volume}")

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, callback=callback):
        while recording:
            sd.sleep(100)

def start_recording():
    global recording, audio_frames, start_time
    recording = True
    audio_frames = []
    start_time = time.time()
    indicator_label.config(text="🟢 Listening", foreground="green")
    logging.info("Recording started.")
    threading.Thread(target=record_audio, daemon=True).start()
    update_timer()

def stop_recording():
    global recording
    recording = False
    indicator_label.config(text="🔴 Stopped", foreground="red")
    logging.info("Recording stopped.")
    save_audio()

# ==============================================================
# SAVE AUDIO
# ==============================================================
def save_audio():
    if not audio_frames:
        return
    try:
        audio = np.concatenate(audio_frames, axis=0)
        reduced = nr.reduce_noise(y=audio.flatten(), sr=SAMPLE_RATE)
        wav.write(FILENAME, SAMPLE_RATE, reduced)
        logging.info("Audio saved successfully.")
        process_audio(FILENAME)
    except Exception as e:
        logging.error(f"Audio save error: {e}")

# ==============================================================
# PROCESS AUDIO
# ==============================================================
def process_audio(file_path):
    full_transcript = ""
    patient_transcript = ""

    try:
        if diarization_pipeline:
            diarization = diarization_pipeline(file_path)
            segments = [(turn.start, turn.end, speaker)
                        for turn, _, speaker in diarization.itertracks(yield_label=True)]
        else:
            segments = [(0, len(audio_frames)/SAMPLE_RATE, "SPEAKER_0")]
    except Exception as e:
        logging.error(f"Diarization failed: {e}")
        segments = [(0, len(audio_frames)/SAMPLE_RATE, "SPEAKER_0")]

    for start, end, speaker in segments:
        try:
            start_sample = int(start * SAMPLE_RATE)
            end_sample = int(end * SAMPLE_RATE)
            segment_audio = np.concatenate(audio_frames, axis=0)[start_sample:end_sample]

            temp_path = os.path.join(tempfile.gettempdir(), f"seg_{speaker}.wav")
            wav.write(temp_path, SAMPLE_RATE, segment_audio)

            result = whisper_model.transcribe(temp_path)
            text = result['text']

            full_transcript += f"[{speaker}] {text}\n"

            if "SPEAKER_0" in speaker:
                patient_transcript += text + " "
        except Exception as e:
            logging.error(f"Segment processing error: {e}")

    transcript_box.delete("1.0", tk.END)
    transcript_box.insert(tk.END, full_transcript)

    diagnosis_text = diagnose_advanced(patient_transcript)

    diagnosis_box.delete("1.0", tk.END)
    diagnosis_box.insert(tk.END, diagnosis_text)

    speak(diagnosis_text)
    save_consultation_history(diagnosis_text)

# ==============================================================
# SAVE HISTORY (NEW)
# ==============================================================
def save_consultation_history(diagnosis_text):
    data = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "duration": timer_label.cget("text"),
        "diagnosis": diagnosis_text
    }
    df = pd.DataFrame([data])
    df.to_csv("consultation_history.csv",
              mode='a',
              header=not os.path.exists("consultation_history.csv"),
              index=False)

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
root.title("Advanced AI Clinical Consultation System")
root.geometry("850x650")

ttk.Label(root, text="Multilingual AI Clinical Consultation System",
          font=("Arial", 16)).pack(pady=10)

indicator_label = ttk.Label(root, text="🔴 Idle", font=("Arial", 12))
indicator_label.pack()

timer_label = ttk.Label(root, text="00:00", font=("Arial", 18))
timer_label.pack()

audio_level_label = ttk.Label(root, text="Audio Level: 0")
audio_level_label.pack()

ttk.Button(root, text="Start Consultation", command=start_recording).pack(pady=5)
ttk.Button(root, text="Stop Consultation", command=stop_recording).pack(pady=5)

ttk.Label(root, text="Transcript").pack()
transcript_box = tk.Text(root, height=12)
transcript_box.pack()

ttk.Label(root, text="AI Preliminary Diagnosis").pack()
diagnosis_box = tk.Text(root, height=8)
diagnosis_box.pack()

root.mainloop()
