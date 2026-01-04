# =========================
# BACKEND - ENGINE
# =========================

import os
import sys
import warnings
import traceback
import threading
import atexit
import time
import json
import random
import math
import wave
import subprocess
import webbrowser
import shutil
from array import array

import pyautogui
import pyttsx3

#dependencia
import tkinter as tk

# =========================
# UTILIDADES
# =========================

def obtener_tamano_carpeta(ruta):
    total = 0
    for ruta_actual, carpetas, archivos in os.walk(ruta):
        for archivo in archivos:
            try:
                total += os.path.getsize(os.path.join(ruta_actual, archivo))
            except Exception:
                pass
    return total


def append_log(text_widget, message):
    text_widget.configure(state="normal")
    text_widget.insert(tk.END, f"{time.strftime('%H:%M:%S')}  {message}\n")
    text_widget.see(tk.END)
    text_widget.configure(state="disabled")


# =========================
# CAPTURA DE ERRORES Y WARNINGS
# =========================

__CAPTURE_ERRORS = []
__CAPTURE_WARNINGS = []

__orig_showwarning = warnings.showwarning
__orig_excepthook = sys.excepthook
__orig_thread_run = threading.Thread.run


def __now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def __custom_showwarning(message, category, filename, lineno, file=None, line=None):
    entry = {
        "time": __now(),
        "message": str(message),
        "category": getattr(category, "_name_", str(category)),
        "filename": filename,
        "lineno": lineno
    }
    __CAPTURE_WARNINGS.append(entry)
    __orig_showwarning(message, category, filename, lineno, file, line)


warnings.showwarning = __custom_showwarning
warnings.filterwarnings("default")


def __custom_excepthook(exc_type, exc_value, exc_tb):
    text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    __CAPTURE_ERRORS.append({"time": __now(), "text": text})
    __orig_excepthook(exc_type, exc_value, exc_tb)


sys.excepthook = __custom_excepthook


def __thread_run_wrapper(self, *args, **kwargs):
    try:
        return __orig_thread_run(self, *args, **kwargs)
    except Exception:
        text = traceback.format_exc()
        __CAPTURE_ERRORS.append({
            "time": __now(),
            "text": text,
            "thread": getattr(self, "name", None)
        })
        print(text, file=sys.stderr)


threading.Thread.run = __thread_run_wrapper


def hook_tk(root):
    def tk_exc_handler(exc_type, exc_value, exc_tb):
        text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        __CAPTURE_ERRORS.append({
            "time": __now(),
            "text": text,
            "where": "tkinter_callback"
        })
        print(text, file=sys.stderr)

    root.report_callback_exception = lambda exc, val, tb: tk_exc_handler(exc, val, tb)


def mostrar_reporte_automatico(verbose=True):
    report = {
        "errors": __CAPTURE_ERRORS,
        "warnings": __CAPTURE_WARNINGS
    }

    print("\n=== REPORTE AUTOMÁTICO ===")
    print(f"Errors: {len(__CAPTURE_ERRORS)}")
    print(f"Warnings: {len(__CAPTURE_WARNINGS)}")
    print("=== FIN REPORTE ===\n")

    if verbose:
        sys.stdout.flush()

    return report


atexit.register(lambda: mostrar_reporte_automatico(True))

# =========================
# TTS
# =========================

tts_engine = pyttsx3.init()

try:
    import pythoncom
    HAS_PYWIN32 = True
except Exception:
    pythoncom = None
    HAS_PYWIN32 = False


def seleccionar_voz_espanol():
    try:
        voz = r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_ES-ES_HELENA_11.0"
        tts_engine.setProperty("voice", voz)
        tts_engine.setProperty("rate", 180)
    except Exception:
        pass


seleccionar_voz_espanol()

# =========================
# AUDIO / VOZ
# =========================

try:
    import pyaudio
    HAS_PYAUDIO = True
except Exception:
    HAS_PYAUDIO = False

try:
    import speech_recognition as sr
    HAS_SPEECHRECOG = True
except Exception:
    HAS_SPEECHRECOG = False


WORK_DIR = os.path.join(os.path.expanduser("~"), "asistente_voz_data")
os.makedirs(WORK_DIR, exist_ok=True)

AUDIO_FILE = os.path.join(WORK_DIR, "captura.wav")
TTS_FILE = os.path.join(WORK_DIR, "respuesta_tts.txt")

# =========================
# MODELO MATEMÁTICO (dBFS)
# =========================

def calcular_calidad_audio_db(wav_path, log_widget=None):
    if not os.path.exists(wav_path):
        return None

    with wave.open(wav_path, 'rb') as wf:
        frames = wf.readframes(wf.getnframes())

    muestras = array('h', frames)
    if not muestras:
        return None

    suma = sum(m * m for m in muestras)
    rms = math.sqrt(suma / len(muestras))
    if rms == 0:
        return -float("inf")

    return 20 * math.log10(rms / 32768.0)

# =========================
# PIPELINE PRINCIPAL
# =========================

def captura_audio(duration_sec, log_widget):
    if not HAS_PYAUDIO:
        with wave.open(AUDIO_FILE, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(b'')
        return True

    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1,
                    rate=16000, input=True, frames_per_buffer=1024)

    frames = []
    for _ in range(int(16000 / 1024 * duration_sec)):
        frames.append(stream.read(1024))

    stream.close()
    p.terminate()

    with wave.open(AUDIO_FILE, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(b''.join(frames))

    return True


def reconocimiento_de_voz(log_widget):
    if not HAS_SPEECHRECOG:
        return random.choice([
            "hola",
            "que hora es",
            "reproduce musica",
            "abre spotify"
        ])

    r = sr.Recognizer()
    with sr.AudioFile(AUDIO_FILE) as src:
        audio = r.record(src)
    return r.recognize_google(audio, language="es-ES")


def procesamiento_de_texto(texto, log_widget):
    texto = texto.lower().strip()
    tokens = texto.split()

    comando = "DESCONOCIDO"
    if "spotify" in tokens:
        comando = "SPOTIFY"

    return {"texto": texto, "tokens": tokens, "comando": comando}


def buscar_respuesta(comando, log_widget):
    respuestas = {
        "SPOTIFY": "Abriendo Spotify",
        "DESCONOCIDO": "No entendí el comando"
    }
    return respuestas.get(comando, "Sin respuesta")


def decision_engine(comando, log_widget):
    return comando


def text_to_speech(texto, log_widget):
    with open(TTS_FILE, "w", encoding="utf-8") as f:
        f.write(texto)

    def _play():
        if HAS_PYWIN32:
            pythoncom.CoInitialize()
        engine = pyttsx3.init()
        engine.say(texto)
        engine.runAndWait()
        engine.stop()
        if HAS_PYWIN32:
            pythoncom.CoUninitialize()

    threading.Thread(target=_play, daemon=True).start()


# =========================
# SPOTIFY
# =========================

RUTA_SPOTIFY_EXE = r"C:\Users\stevl\AppData\Roaming\Spotify\Spotify.exe"
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05


def spotify_reproducir(cancion, log_widget):
    try:
        os.startfile(RUTA_SPOTIFY_EXE)
        return f"Reproduciendo {cancion}"
    except Exception:
        webbrowser.open("https://open.spotify.com")
        return "Spotify Web abierto"
