import os

def obtener_tamano_carpeta(ruta):
    total = 0
    for ruta_actual, carpetas, archivos in os.walk(ruta):
        for archivo in archivos:
            try:
                total += os.path.getsize(os.path.join(ruta_actual, archivo))
            except:
                pass
    return total

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
from pyautogui import getWindowsWithTitle
import threading
import time
import os
import shutil
import random
import wave
import webbrowser   
import subprocess
import pyautogui
import pyttsx3
import math
from array import array

import time
start_time = time.time()

import time
compile_start = time.time()

# === INICIO: Captura automática de ERRORS y WARNINGS ===
import sys, warnings, traceback, threading, atexit, time as time_mod, json

__CAPTURE_ERRORS = []
__CAPTURE_WARNINGS = []

__orig_showwarning = warnings.showwarning
__orig_excepthook = sys.excepthook
__orig_thread_run = threading.Thread.run


def __now():
    return time_mod.strftime("%Y-%m-%d %H:%M:%S")


def __custom_showwarning(message, category, filename, lineno, file=None, line=None):
    entry = {
        "time": __now(),
        "message": str(message),
        "category": getattr(category, "_name_", str(category)),
        "filename": filename,
        "lineno": lineno,
        "line": line
    }
    __CAPTURE_WARNINGS.append(entry)

    try:
        __orig_showwarning(message, category, filename, lineno, file, line)
    except Exception:
        
        print(f"[warning] {entry}", file=sys.stderr)


warnings.showwarning = __custom_showwarning
warnings.filterwarnings("default")


def __custom_excepthook(exc_type, exc_value, exc_tb):
    text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    entry = {"time": __now(), "text": text}
    __CAPTURE_ERRORS.append(entry)
   
    try:
        __orig_excepthook(exc_type, exc_value, exc_tb)
    except Exception:
        print(text, file=sys.stderr)


sys.excepthook = __custom_excepthook


def __thread_run_wrapper(self, *args, **kwargs):
    try:
        return __orig_thread_run(self, *args, **kwargs)
    except Exception:
        text = traceback.format_exc()
        entry = {"time": __now(), "text": text, "thread_name": getattr(self, "name", None)}
        __CAPTURE_ERRORS.append(entry)
        print(text, file=sys.stderr)
        return None


threading.Thread.run = __thread_run_wrapper


def hook_tk(root):
    def tk_exc_handler(exc_type, exc_value, exc_tb):
        text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        __CAPTURE_ERRORS.append({"time": __now(), "text": text, "where": "tkinter_callback"})
        print("[TK EXCEPTION]\n" + text, file=sys.stderr)

    try:
        root.report_callback_exception = lambda exc, val, tb: tk_exc_handler(exc, val, tb)
    except Exception:
        pass


def mostrar_reporte_automatico(verbose=True):
    report = {
        "errors_count": len(__CAPTURE_ERRORS),
        "warnings_count": len(__CAPTURE_WARNINGS),
        "errors": list(__CAPTURE_ERRORS),
        "warnings": list(__CAPTURE_WARNINGS)
    }

    print("\n=== REPORTE AUTOMÁTICO ===")
    print(f"Errors: {report['errors_count']}")
    print(f"Warnings: {report['warnings_count']}")
    if report['errors_count'] > 0:
        print("\n--- ERRORES DETALLADOS ---")
        for i, e in enumerate(report['errors'], 1):
            print(f"[{i}] {e.get('time')}:\n{e.get('text')}\n")
    if report['warnings_count'] > 0:
        print("\n--- WARNINGS DETALLADOS ---")
        for i, w in enumerate(report['warnings'], 1):
            print(f"[{i}] {w.get('time')} {w.get('filename')}:{w.get('lineno')} "
                  f"{w.get('category')}: {w.get('message')}")
    print("=== FIN REPORTE ===\n")

    if verbose:
        sys.stdout.flush()
    return report


def mostrar_reporte_en_log(log_widget):
    """
    Añade el resumen al widget log_widget (de tipo ScrolledText).
    """
    try:
        rep = mostrar_reporte_automatico(verbose=False)
        header = f"REPORT -> Errors: {rep['errors_count']}  Warnings: {rep['warnings_count']}\n"
        log_widget.configure(state="normal")
        log_widget.insert(tk.END, header)
        if rep['errors_count'] > 0:
            log_widget.insert(tk.END, "--- ERRORES ---\n")
            for e in rep['errors']:
                texto = e.get('text', '').strip()[:1000]
                log_widget.insert(tk.END, f"{e.get('time')}: {texto}\n\n")
        if rep['warnings_count'] > 0:
            log_widget.insert(tk.END, "--- WARNINGS ---\n")
            for w in rep['warnings']:
                log_widget.insert(tk.END,
                                  f"{w.get('time')} {w.get('filename')}:{w.get('lineno')} "
                                  f"{w.get('category')}: {w.get('message')}\n")
        log_widget.see(tk.END)
        log_widget.configure(state="disabled")
    except Exception as e:
        print("Error mostrando reporte en log:", e, file=sys.stderr)


atexit.register(lambda: mostrar_reporte_automatico(verbose=True))

# === FIN: Captura automática de ERRORS y WARNINGS ===

tts_engine = pyttsx3.init()

try:
    import pythoncom
    HAS_PYWIN32 = True
except Exception:
    pythoncom = None
    HAS_PYWIN32 = False


def seleccionar_voz_espanol():
    try:
        voz_helena = "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_ES-ES_HELENA_11.0"
        tts_engine.setProperty('voice', voz_helena)
        tts_engine.setProperty('rate', 180)
        print("✔ Voz Helena seleccionada (engine global).")
    except Exception as e:
        print("⚠ No se pudo asignar la voz Helena al engine global:", e)


seleccionar_voz_espanol()

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

SPOTIFY_QUERY = ""
RUTA_SPOTIFY_EXE = r"C:\Users\stevl\AppData\Roaming\Spotify\Spotify.exe"

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05


class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, event=None):
        if self.tooltip:
            return
        x = self.widget.winfo_rootx() + 40
        y = self.widget.winfo_rooty() + 20

        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")

        label = tk.Label(
            self.tooltip,
            text=self.text,
            background="#ffffe0",
            relief="solid",
            borderwidth=1,
            font=("Arial", 9)
        )
        label.pack(ipadx=5, pady=2)

    def hide(self, event=None):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None


def append_log(text_widget, message):
    text_widget.configure(state="normal")
    text_widget.insert(tk.END, f"{time.strftime('%H:%M:%S')}  {message}\n")
    text_widget.see(tk.END)
    text_widget.configure(state="disabled")



#   MODELO MATEMÁTICO: CALIDAD EN DECIBELES 

def calcular_calidad_audio_db(wav_path, log_widget=None):
    """
    Calcula el nivel RMS del audio y lo expresa en dBFS
    usando el modelo:
        A_rms = sqrt( (1/N) * sum(x[n]^2) )
        L_dB = 20 * log10( A_rms / A_ref )
    donde A_ref = 32768 (máximo de int16).
    """
    if not os.path.exists(wav_path) or os.path.getsize(wav_path) == 0:
        if log_widget:
            append_log(log_widget, "No se puede calcular dB: archivo inexistente o vacío.")
        return None

    try:
        with wave.open(wav_path, 'rb') as wf:
            nframes = wf.getnframes()
            sampwidth = wf.getsampwidth()

            if sampwidth != 2:
                if log_widget:
                    append_log(log_widget, f"Ancho de muestra no soportado para dB (sampwidth={sampwidth}).")
                return None

            raw_frames = wf.readframes(nframes)

        muestras = array('h', raw_frames)  

        if len(muestras) == 0:
            if log_widget:
                append_log(log_widget, "No hay muestras de audio para calcular RMS.")
            return None

        suma_cuadrados = 0.0
        for m in muestras:
            suma_cuadrados += m * m

        N = len(muestras)
        A_rms = math.sqrt(suma_cuadrados / N)

        A_ref = 32768.0
        if A_rms == 0:
            if log_widget:
                append_log(log_widget, "RMS = 0 (silencio). Nivel ≈ -∞ dBFS.")
            return -float('inf')

        L_dB = 20.0 * math.log10(A_rms / A_ref)

        if log_widget:
            append_log(log_widget, f"   • RMS: {A_rms:.2f}")
            append_log(log_widget, f"   • Nivel aproximado: {L_dB:.2f} dBFS")

        return L_dB

    except Exception as e:
        if log_widget:
            append_log(log_widget, f"Error calculando calidad en dB: {e}")
        return None



#   PROCESO 1: CAPTURA + PREPROCESAMIENTO

def captura_audio(duration_sec, log_widget):
    append_log(log_widget, f"🎤 Iniciando captura de audio ({duration_sec}s)...")

    if not HAS_PYAUDIO:
        time.sleep(2)
        append_log(log_widget, " MODO SIMULADO: audio grabado.")
        with wave.open(AUDIO_FILE, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(b'')
        return True

    try:
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 16000

        p = pyaudio.PyAudio()
        info = p.get_default_input_device_info()
        append_log(log_widget, f" Usando micrófono: {info['name']}")

        stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK)

        append_log(log_widget, "Grabando... Habla ahora!")
        frames = []
        for _ in range(0, int(RATE / CHUNK * duration_sec)):
            frames.append(stream.read(CHUNK))

        stream.stop_stream()
        stream.close()
        p.terminate()

        with wave.open(AUDIO_FILE, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))

        append_log(log_widget, f" Audio guardado: {AUDIO_FILE}")
        return True

    except Exception as e:
        append_log(log_widget, f" Error: {e}")
        return False


def preprocesamiento_audio(log_widget):
    append_log(log_widget, "🛠 Iniciando preprocesamiento...")

    if not os.path.exists(AUDIO_FILE):
        append_log(log_widget, "No existe el archivo de audio.")
        return False

    try:
        with wave.open(AUDIO_FILE, 'rb') as wf:
            duration = wf.getnframes() / float(wf.getframerate())
            sr = wf.getframerate()
            channels = wf.getnchannels()

        append_log(log_widget, f"   • Duración: {duration:.2f}s")
        append_log(log_widget, f"   • Sample rate: {sr} Hz")
        append_log(log_widget, f"   • Canales: {channels}")

        # 🔊 Aplicamos el modelo matemático 2 (RMS + dBFS)
        nivel_db = calcular_calidad_audio_db(AUDIO_FILE, log_widget)
        if nivel_db is not None:
            if nivel_db == -float('inf'):
                append_log(log_widget, "   • Calidad (nivel RMS): -∞ dBFS (silencio).")
            else:
                append_log(log_widget, f"   • Calidad (nivel RMS): {nivel_db:.2f} dBFS")

        append_log(log_widget, " Preprocesamiento completado.")
        return True
    except Exception as e:
        append_log(log_widget, f"Error: {e}")
        return False



#   PROCESO 2: RECONOCIMIENTO DE VOZ

def reconocimiento_de_voz(log_widget):
    append_log(log_widget, "🗣 Reconociendo voz...")

    if not os.path.exists(AUDIO_FILE) or os.path.getsize(AUDIO_FILE) == 0:
        append_log(log_widget, "No hay audio válido.")
        return ""

    # MODO SIMULADO
    if not HAS_SPEECHRECOG:
        ejemplos = [
            "hola como estas",
            "cual es la fecha de hoy",
            "cuanto es 10 mas 5",
            "enciende la luz",
            "apaga la luz",
            "que es un atomo"
        ]
        texto = random.choice(ejemplos)
        append_log(log_widget, f" Modo simulado: '{texto}'")
        return texto

    try:
        r = sr.Recognizer()
        with sr.AudioFile(AUDIO_FILE) as src:
            r.adjust_for_ambient_noise(src)
            audio = r.record(src)
        texto = r.recognize_google(audio, language="es-ES")
        append_log(log_widget, f"Transcripción: '{texto}'")
        return texto
    except Exception:
        append_log(log_widget, "Error reconociendo audio.")
        return ""



#   PROCESO 3: NLU

def procesamiento_de_texto(texto, log_widget):
    global SPOTIFY_QUERY

    append_log(log_widget, "📄 Procesando texto...")

    if not texto:
        return {"texto": "", "keywords": [], "comando": "NONE"}

    texto_limpio = texto.lower().strip()
    limpio = "".join([c if c.isalnum() or c == " " else " " for c in texto_limpio])
    tokens = limpio.split()

    comunes = {"el", "la", "los", "las", "de", "del", "es", "en", "un", "una", "por",
               "que", "cuál", "cual"}
    keywords = [t for t in tokens if t not in comunes]

    comando = "DESCONOCIDO"

    if ("spotify" in tokens or "spotify" in texto_limpio) and any(
            w in tokens for w in ["abre", "abrir", "abrirla", "abrirlo"]):
        comando = "ABRIR_SPOTIFY"

    elif any(w in tokens for w in ["reproduce", "pon", "reproducir"]) and "spotify" in texto_limpio:
        comando = "SPOTIFY_PLAY"

    elif texto_limpio.startswith(("reproduce ", "pon ", "reproducir ")):
        q = texto_limpio
        for prefix in ("reproduce ", "pon ", "reproducir "):
            if q.startswith(prefix):
                q = q[len(prefix):].strip()
                break
        if q:
            SPOTIFY_QUERY = q
            comando = "SPOTIFY_BUSCAR"

    elif "enciende" in keywords:
        comando = "ENCENDER"
    elif "apaga" in keywords:
        comando = "APAGAR"
    elif "abre" in keywords:
        comando = "ABRIR"
    elif "cierra" in keywords:
        comando = "CERRAR"
    elif "hora" in keywords or "tiempo" in keywords:
        comando = "HORA"
    elif "fecha" in keywords or "día" in keywords or "dia" in keywords:
        comando = "FECHA"
    elif any(k in keywords for k in ["hola", "buenas", "saludos"]):
        comando = "SALUDO"
    elif "gracias" in keywords:
        comando = "AGRADECIMIENTO"
    elif "cuanto" in keywords or "cuánto" in keywords or any(
            k in keywords for k in ["suma", "resta", "multiplica", "divide"]):
        comando = "MATEMATICA"
    elif texto_limpio.startswith("que es") or texto_limpio.startswith("qué es"):
        comando = "DEFINICION"
    elif texto_limpio.startswith("quien es") or texto_limpio.startswith("quién es"):
        comando = "PERSONA"

    append_log(log_widget, f" Keywords: {keywords}")
    append_log(log_widget, f" Comando detectado: {comando}")

    return {
        "texto": texto_limpio,
        "keywords": keywords,
        "comando": comando
    }



#   PROCESO 4: BASE DE CONOCIMIENTO

def buscar_respuesta(comando, log_widget):
    append_log(log_widget, f"🔎 Buscando respuesta para {comando}...")

    if comando == "HORA":
        return time.strftime("Son las %H:%M:%S.")

    if comando == "FECHA":
        return time.strftime("Hoy es %A %d de %B del %Y.")

    if comando == "SALUDO":
        return random.choice([
            "Hola, ¿cómo puedo ayudarte?",
            "¡Hola! ¿Qué deseas?",
            "Saludos, estoy a tu servicio."
        ])

    if comando == "AGRADECIMIENTO":
        return random.choice([
            "Con gusto.",
            "Para servirte.",
            "No hay de qué."
        ])

    # Spotify responses
    if comando == "ABRIR_SPOTIFY":
        return "Abriendo Spotify."
    if comando == "SPOTIFY_PLAY":
        return "Reproduciendo Spotify."
    if comando == "SPOTIFY_BUSCAR":
        return f"Buscando en Spotify: {SPOTIFY_QUERY}"

    if comando == "DEFINICION":
        return "Puedo responder preguntas básicas, pero no tengo conocimiento enciclopédico avanzado."

    if comando == "PERSONA":
        return "No tengo información biográfica, pero puedo ayudarte con funciones básicas."

    if comando == "MATEMATICA":
        return "Lo siento, las matemáticas avanzadas aún no están implementadas."

    if comando == "ENCENDER":
        return "Encendiendo el dispositivo."

    if comando == "APAGAR":
        return "Apagando el dispositivo."

    if comando == "ABRIR":
        return "Abriendo ahora mismo."

    if comando == "CERRAR":
        return "Cerrando ahora mismo."

    if comando == "NONE":
        return "No escuché nada útil."

    return "No entendí bien la orden."



#   PROCESO 5: DECISIONES

def decision_engine(comando, log_widget):
    if comando in ["ENCENDER", "APAGAR", "ABRIR", "CERRAR",
                   "ABRIR_SPOTIFY", "SPOTIFY_PLAY", "SPOTIFY_BUSCAR"]:
        accion = comando
    else:
        accion = "NINGUNA"

    append_log(log_widget, f"⚙ Acción decidida: {accion}")
    return accion


def ejecutar_flujo(accion, log_widget):
    append_log(log_widget, f"Ejecutando flujo: {accion}")


def gestionar_accion(accion, log_widget):
    append_log(log_widget, f"Acción gestionada: {accion}")



#   PROCESO 6: TTS

def text_to_speech(texto, log_widget):
    # Guardado del texto (comportamiento original)
    with open(TTS_FILE, "w", encoding="utf-8") as f:
        f.write(texto)

    append_log(log_widget, f"🔊 Respuesta guardada en: {TTS_FILE}")

    try:
        def _play():
            if HAS_PYWIN32 and pythoncom:
                try:
                    pythoncom.CoInitialize()
                except Exception:
                    pass

            try:
                engine_local = pyttsx3.init(driverName='sapi5')
                voz_helena = "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_ES-ES_HELENA_11.0"
                engine_local.setProperty('voice', voz_helena)
                engine_local.setProperty('rate', 180)
                engine_local.say(texto)
                engine_local.runAndWait()
                engine_local.stop()
                append_log(log_widget, "Voz reproducida correctamente (thread-safe).")
            except Exception as e:
                append_log(log_widget, f"Error síntesis (thread): {e}")
            finally:
                if HAS_PYWIN32 and pythoncom:
                    try:
                        pythoncom.CoUninitialize()
                    except Exception:
                        pass

        threading.Thread(target=_play, daemon=True).start()
    except Exception as e:
        append_log(log_widget, f"Error al lanzar hilo TTS: {e}")



#   SPOTIFY
def spotify_reproducir(cancion, log_widget, espera_segundos=3):
    try:
        append_log(log_widget, f"🎧 spotify_reproducir: solicitada -> '{cancion}'")

        try:
            subprocess.Popen([RUTA_SPOTIFY_EXE])
            append_log(log_widget, f"Spotify.exe lanzado desde: {RUTA_SPOTIFY_EXE}")
        except Exception as e:
            append_log(log_widget, f"No se pudo abrir Spotify.exe: {e}. Intentando os.startfile...")
            try:
                os.startfile(RUTA_SPOTIFY_EXE)
            except Exception as e2:
                append_log(log_widget, f"Falló abrir app: {e2}. Abriendo Spotify Web.")
                webbrowser.open("https://open.spotify.com")
                return "Abriendo Spotify Web (no se pudo abrir la app)."

        time.sleep(3)

        try:
            ventanas = getWindowsWithTitle("Spotify")
            if ventanas:
                v = ventanas[0]
                try:
                    v.activate()
                    time.sleep(0.4)
                    v.maximize()
                    time.sleep(0.4)
                    append_log(log_widget, "Spotify fue traído al frente correctamente.")
                except Exception:
                    pass
            else:
                append_log(log_widget, "No se encontró la ventana de Spotify para activarla.")
        except Exception as e:
            append_log(log_widget, f"No se pudo forzar primer plano: {e}")

        pyautogui.hotkey("ctrl", "l")
        time.sleep(0.40)

        pyautogui.typewrite(cancion, interval=0.04)
        time.sleep(0.50)
        pyautogui.press('enter')

        time.sleep(1.20)

        for _ in range(3):
            pyautogui.press("tab")
            time.sleep(0.13)

        pyautogui.press("enter")

        append_log(log_widget, f"🎶 Reproduciendo: {cancion}")
        return f"Reproduciendo {cancion} en Spotify Desktop."

    except Exception as e:
        append_log(log_widget, f"Error general spotify_reproducir: {e}")
        return "Error intentando reproducir en Spotify."



#   PROCESO 7: ACTUACIÓN EN ENTORNO

def act_on_world(accion, log_widget):
    global SPOTIFY_QUERY

    if accion == "NINGUNA":
        append_log(log_widget, "No hay acción física que ejecutar.")
        return

    if accion == "ABRIR_SPOTIFY":
        append_log(log_widget, "Acción: abrir Spotify...")
        try:
            os.startfile(RUTA_SPOTIFY_EXE)
            append_log(log_widget, "Spotify: app abierta (os.startfile).")
        except Exception as e:
            append_log(log_widget, f"No se pudo abrir app: {e}. Abriendo Spotify Web...")
            webbrowser.open("https://open.spotify.com")
        return

    if accion == "SPOTIFY_PLAY":
        append_log(log_widget, "Acción: reproducir Spotify (playlist por defecto)...")
        try:
            uri_playlist = "spotify:playlist:37i9dQZF1DXcBWIGoYBM5M"
            os.startfile(uri_playlist)
            append_log(log_widget, f"Intentando reproducir playlist por URI: {uri_playlist}")
        except Exception as e:
            append_log(log_widget, f"No se pudo abrir URI en app: {e}. Abriendo playlist en web...")
            playlist = "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M"
            webbrowser.open(playlist)
            append_log(log_widget, f"Abriendo playlist web: {playlist}")
        return

    if accion == "SPOTIFY_BUSCAR":
        if not SPOTIFY_QUERY:
            append_log(log_widget, "No hay término de búsqueda para Spotify.")
            return
        append_log(log_widget, f"Acción: search & play -> {SPOTIFY_QUERY}")
        resultado = spotify_reproducir(SPOTIFY_QUERY, log_widget, espera_segundos=3.5)
        append_log(log_widget, resultado)
        return

    append_log(log_widget, f"Simulando ejecución física de: {accion}")



#   PROCESO 8: INTERACCIÓN CON INGENIERO

def mostrar_diagnostico(log_widget, contexto):
    append_log(log_widget, "🧪 Estado del sistema:")
    append_log(log_widget, f"Mensajes en contexto: {len(contexto)}")


def generar_reporte(contexto, log_widget):
    append_log(log_widget, f"Reporte: {contexto}")


def optimizar_modelo(log_widget):
    append_log(log_widget, "Optimizando modelo (simulado)...")



#   GUI

class AsistenteGUI:
    def __init__(self, root):
        self.root = root
        root.title("Asistente de Voz Inteligente - Opción B")
        root.geometry("1100x650")

        self.last_transcription = ""
        self.last_processed = None
        self.last_response = ""
        self.last_action = ""
        self.contexto = []

        self.setup_ui()

    def setup_ui(self):
        main = ttk.Frame(self.root, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text="🚘 ASISTENTE DE VOZ - MERCEDES",
                  font=("Arial", 16, "bold")).pack(pady=10)

        # DURACIÓN
        top = ttk.Frame(main)
        top.pack(fill=tk.X)
        ttk.Label(top, text="Duración (s):").pack(side=tk.LEFT)
        self.duracion_var = tk.IntVar(value=5)
        ttk.Entry(top, textvariable=self.duracion_var, width=5).pack(side=tk.LEFT, padx=5)

        ttk.Button(top, text="Cargar audio externo", command=self.cargar_audio_archivo) \
            .pack(side=tk.LEFT, padx=10)

        # PROCESOS
        procesos = ttk.LabelFrame(main, text="Procesos", padding=10)
        procesos.pack(fill=tk.X, pady=10)

        # ---- BOTONES ----
        self.bot(procesos, "1. Capturar Audio", self.run_proceso_1,
                 "Captura el audio y lo prepara para análisis")
        self.bot(procesos, "2. Autenticar Voz", self.run_proceso_2,
                 "Convierte el audio en texto")
        self.bot(procesos, "3. Procesar Texto", self.run_proceso_3,
                 "Extrae intención, comandos y palabras clave")
        self.bot(procesos, "4. Consultar en DB", self.run_proceso_4,
                 "Busca respuesta en la base de conocimiento")
        self.bot(procesos, "5. Gestionar Accion", self.run_proceso_5,
                 "Determina qué acción tomar")
        self.bot(procesos, "6. Generar Audio-Respuesta", self.run_proceso_6,
                 "Convierte la respuesta en voz real")
        self.bot(procesos, "7. Procesar Comando", self.run_proceso_7,
                 "Simula actuar sobre un dispositivo")
        self.bot(procesos, "8. Mostrar Diagnostico", self.run_proceso_8,
                 "Muestra diagnósticos y reportes")

        log_frame = ttk.LabelFrame(main, text="LOG / REGISTRO", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_widget = scrolledtext.ScrolledText(log_frame, height=15,
                                                    state="disabled",
                                                    font=("Consolas", 9))
        self.log_widget.pack(fill=tk.BOTH, expand=True)

        text_frame = ttk.LabelFrame(main, text="Texto procesado", padding=10)
        text_frame.pack(fill=tk.BOTH)

        self.texto_widget = scrolledtext.ScrolledText(text_frame, height=6)
        self.texto_widget.pack(fill=tk.BOTH, expand=True)

        pie = ttk.Frame(main)
        pie.pack(fill=tk.X, pady=5)
        ttk.Button(pie, text="Limpiar log", command=self.limpiar_log) \
            .pack(side=tk.RIGHT, padx=5)
        ttk.Button(pie, text="Ver info audio", command=self.ver_info_audio) \
            .pack(side=tk.RIGHT, padx=5)

        append_log(self.log_widget, "Sistema iniciado.")
        if not HAS_PYAUDIO:
            append_log(self.log_widget, "PyAudio no disponible (modo simulado).")
        if not HAS_SPEECHRECOG:
            append_log(self.log_widget, "SpeechRecognition no disponible (modo simulado).")

    def bot(self, parent, text, cmd, help_text):
        b = ttk.Button(parent, text=text, command=self.threaded(cmd))
        b.pack(fill=tk.X, pady=2)
        ToolTip(b, help_text)
        return b

    def threaded(self, fn):
        def wrapper():
            threading.Thread(target=fn, daemon=True).start()
        return wrapper

    def run_proceso_1(self):
        dur = max(1, int(self.duracion_var.get()))
        if captura_audio(dur, self.log_widget):
            preprocesamiento_audio(self.log_widget)

    def run_proceso_2(self):
        texto = reconocimiento_de_voz(self.log_widget)
        self.last_transcription = texto
        if texto:
            self.texto_widget.delete(1.0, tk.END)
            self.texto_widget.insert(tk.END, texto)

    def run_proceso_3(self):
        texto = self.texto_widget.get(1.0, tk.END).strip() or self.last_transcription
        if not texto:
            append_log(self.log_widget, "No hay texto para procesar.")
            return
        self.last_processed = procesamiento_de_texto(texto, self.log_widget)
        self.contexto.append(self.last_processed["texto"])
        resumen = (
            f"TEXTO: {self.last_processed['texto']}\n"
            f"COMANDO: {self.last_processed['comando']}\n"
            f"KEYWORDS: {self.last_processed['keywords']}\n"
        )
        self.texto_widget.delete(1.0, tk.END)
        self.texto_widget.insert(tk.END, resumen)

    def run_proceso_4(self):
        if not self.last_processed:
            append_log(self.log_widget, "Ejecuta el Proceso 3 primero.")
            return
        comando = self.last_processed["comando"]
        self.last_response = buscar_respuesta(comando, self.log_widget)
        self.texto_widget.delete(1.0, tk.END)
        self.texto_widget.insert(tk.END, self.last_response)

    def run_proceso_5(self):
        if not self.last_processed:
            append_log(self.log_widget, "Ejecuta el Proceso 3 primero.")
            return
        self.last_action = decision_engine(self.last_processed["comando"], self.log_widget)
        ejecutar_flujo(self.last_action, self.log_widget)
        gestionar_accion(self.last_action, self.log_widget)

    def run_proceso_6(self):
        if not self.last_response:
            append_log(self.log_widget, "No hay respuesta para sintetizar.")
            return

        text_to_speech(self.last_response, self.log_widget)

    def run_proceso_7(self):
        act_on_world(self.last_action, self.log_widget)

    def run_proceso_8(self):
        mostrar_diagnostico(self.log_widget, self.contexto)
        generar_reporte(self.contexto, self.log_widget)
        optimizar_modelo(self.log_widget)

    def cargar_audio_archivo(self):
        path = filedialog.askopenfilename(
            filetypes=[("WAV", ".wav"), ("Todos", ".*")]
        )
        if path:
            shutil.copy2(path, AUDIO_FILE)
            append_log(self.log_widget, f"Archivo cargado: {path}")

    def ver_info_audio(self):
        if not os.path.exists(AUDIO_FILE):
            messagebox.showinfo("Audio", "No existe archivo.")
            return
        size = os.path.getsize(AUDIO_FILE)
        info = f"Archivo: {AUDIO_FILE}\nTamaño: {size} bytes\n"
        try:
            with wave.open(AUDIO_FILE, 'rb') as wf:
                dur = wf.getnframes() / float(wf.getframerate())
                info += f"Duración: {dur:.2f}s\n"
        except Exception:
            info += "Error leyendo WAV.\n"

        # Usamos el mismo modelo de dB
        nivel_db = calcular_calidad_audio_db(AUDIO_FILE, self.log_widget)
        if nivel_db is not None:
            if nivel_db == -float('inf'):
                info += "Nivel aprox.: -∞ dBFS (silencio)"
            else:
                info += f"Nivel aprox.: {nivel_db:.2f} dBFS"

        messagebox.showinfo("Audio", info)

    def limpiar_log(self):
        self.log_widget.configure(state="normal")
        self.log_widget.delete(1.0, tk.END)
        self.log_widget.configure(state="disabled")
        append_log(self.log_widget, "Log limpio.")



compile_end = time.time()
compile_time = compile_end - compile_start

print(f"[OK] Tiempo de compilación: {compile_time:.4f} segundos")



#   MAIN

def main():
    root = tk.Tk()
    hook_tk(root)
    AsistenteGUI(root)
    root.mainloop()

def main():
    root = tk.Tk()
    hook_tk(root)                 
    AsistenteGUI(root)
    root.mainloop()

    end_time = time.time()
    execution_time = end_time - compile_end
    print(f"[OK] Tiempo de ejecución: {execution_time:.4f} segundos")

carpeta_codigo = os.path.dirname(os.path.abspath(__file__))  # carpeta donde está tu código
tam = obtener_tamano_carpeta(carpeta_codigo)

print(f"Output Size: {tam/1024/1024:.2f} MB")

if __name__ == "__main__":
    main()