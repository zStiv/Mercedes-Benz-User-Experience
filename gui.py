# =========================
# FRONTEND - GUI
# =========================
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
import os
import shutil
import wave

# ===== IMPORTS DEL BACKEND =====
from engine import (
    captura_audio,
    preprocesamiento_audio,
    reconocimiento_de_voz,
    procesamiento_de_texto,
    buscar_respuesta,
    decision_engine,
    ejecutar_flujo,
    gestionar_accion,
    text_to_speech,
    act_on_world,
    mostrar_diagnostico,
    generar_reporte,
    optimizar_modelo,
    calcular_calidad_audio_db,
    hook_tk,
    AUDIO_FILE,
    HAS_PYAUDIO,
    HAS_SPEECHRECOG
)

# ===============================
# UTILIDADES DE UI
# ===============================

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
    text_widget.insert(tk.END, message + "\n")
    text_widget.see(tk.END)
    text_widget.configure(state="disabled")


# ===============================
# CLASE PRINCIPAL DE GUI
# ===============================

class AsistenteGUI:
    def __init__(self, root):
        self.root = root
        root.title("Asistente de Voz Inteligente - Mercedes")
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

        ttk.Label(
            main,
            text="🚘 ASISTENTE DE VOZ - MERCEDES",
            font=("Arial", 16, "bold")
        ).pack(pady=10)

        # =======================
        # CONFIGURACIÓN SUPERIOR
        # =======================
        top = ttk.Frame(main)
        top.pack(fill=tk.X)

        ttk.Label(top, text="Duración (s):").pack(side=tk.LEFT)
        self.duracion_var = tk.IntVar(value=5)
        ttk.Entry(top, textvariable=self.duracion_var, width=5).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            top,
            text="Cargar audio externo",
            command=self.cargar_audio_archivo
        ).pack(side=tk.LEFT, padx=10)

        # =======================
        # BOTONES DE PROCESOS
        # =======================
        procesos = ttk.LabelFrame(main, text="Procesos", padding=10)
        procesos.pack(fill=tk.X, pady=10)

        self.bot(procesos, "1. Capturar Audio", self.run_proceso_1,
                 "Captura el audio y lo prepara")
        self.bot(procesos, "2. Autenticar Voz", self.run_proceso_2,
                 "Convierte audio a texto")
        self.bot(procesos, "3. Procesar Texto", self.run_proceso_3,
                 "Detecta intención y comando")
        self.bot(procesos, "4. Consultar en DB", self.run_proceso_4,
                 "Busca una respuesta")
        self.bot(procesos, "5. Gestionar Acción", self.run_proceso_5,
                 "Decide qué hacer")
        self.bot(procesos, "6. Generar Voz", self.run_proceso_6,
                 "Texto a voz")
        self.bot(procesos, "7. Ejecutar Acción", self.run_proceso_7,
                 "Actúa en el sistema")
        self.bot(procesos, "8. Diagnóstico", self.run_proceso_8,
                 "Estado interno")

        # =======================
        # LOG
        # =======================
        log_frame = ttk.LabelFrame(main, text="LOG / REGISTRO", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_widget = scrolledtext.ScrolledText(
            log_frame,
            height=15,
            state="disabled",
            font=("Consolas", 9)
        )
        self.log_widget.pack(fill=tk.BOTH, expand=True)

        # =======================
        # TEXTO PROCESADO
        # =======================
        text_frame = ttk.LabelFrame(main, text="Texto procesado", padding=10)
        text_frame.pack(fill=tk.BOTH)

        self.texto_widget = scrolledtext.ScrolledText(text_frame, height=6)
        self.texto_widget.pack(fill=tk.BOTH, expand=True)

        # =======================
        # PIE
        # =======================
        pie = ttk.Frame(main)
        pie.pack(fill=tk.X, pady=5)

        ttk.Button(pie, text="Limpiar log", command=self.limpiar_log)\
            .pack(side=tk.RIGHT, padx=5)

        ttk.Button(pie, text="Ver info audio", command=self.ver_info_audio)\
            .pack(side=tk.RIGHT, padx=5)

        append_log(self.log_widget, "Sistema iniciado.")

        if not HAS_PYAUDIO:
            append_log(self.log_widget, "PyAudio no disponible (modo simulado).")
        if not HAS_SPEECHRECOG:
            append_log(self.log_widget, "SpeechRecognition no disponible (modo simulado).")

    # =======================
    # HELPERS
    # =======================

    def bot(self, parent, text, cmd, help_text):
        b = ttk.Button(parent, text=text, command=self.threaded(cmd))
        b.pack(fill=tk.X, pady=2)
        ToolTip(b, help_text)
        return b

    def threaded(self, fn):
        def wrapper():
            threading.Thread(target=fn, daemon=True).start()
        return wrapper

    # =======================
    # PROCESOS (LLAMAN BACKEND)
    # =======================

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
            append_log(self.log_widget, "No hay texto.")
            return
        self.last_processed = procesamiento_de_texto(texto, self.log_widget)
        self.contexto.append(self.last_processed["texto"])

    def run_proceso_4(self):
        if not self.last_processed:
            append_log(self.log_widget, "Ejecuta el proceso 3.")
            return
        self.last_response = buscar_respuesta(
            self.last_processed["comando"],
            self.log_widget
        )
        self.texto_widget.delete(1.0, tk.END)
        self.texto_widget.insert(tk.END, self.last_response)

    def run_proceso_5(self):
        self.last_action = decision_engine(
            self.last_processed["comando"],
            self.log_widget
        )
        ejecutar_flujo(self.last_action, self.log_widget)
        gestionar_accion(self.last_action, self.log_widget)

    def run_proceso_6(self):
        text_to_speech(self.last_response, self.log_widget)

    def run_proceso_7(self):
        act_on_world(self.last_action, self.log_widget)

    def run_proceso_8(self):
        mostrar_diagnostico(self.log_widget, self.contexto)
        generar_reporte(self.contexto, self.log_widget)
        optimizar_modelo(self.log_widget)

    # =======================
    # EXTRAS UI
    # =======================

    def cargar_audio_archivo(self):
        path = filedialog.askopenfilename(
            filetypes=[("WAV", ".wav"), ("Todos", ".*")]
        )
        if path:
            shutil.copy2(path, AUDIO_FILE)
            append_log(self.log_widget, f"Audio cargado: {path}")

    def ver_info_audio(self):
        if not os.path.exists(AUDIO_FILE):
            messagebox.showinfo("Audio", "No existe archivo.")
            return

        size = os.path.getsize(AUDIO_FILE)
        info = f"Tamaño: {size} bytes\n"

        try:
            with wave.open(AUDIO_FILE, 'rb') as wf:
                dur = wf.getnframes() / float(wf.getframerate())
                info += f"Duración: {dur:.2f}s\n"
        except Exception:
            info += "Error leyendo WAV\n"

        nivel_db = calcular_calidad_audio_db(AUDIO_FILE, self.log_widget)
        if nivel_db is not None:
            info += f"Nivel: {nivel_db:.2f} dBFS"

        messagebox.showinfo("Audio", info)

    def limpiar_log(self):
        self.log_widget.configure(state="normal")
        self.log_widget.delete(1.0, tk.END)
        self.log_widget.configure(state="disabled")
        append_log(self.log_widget, "Log limpio.")


# ===============================
# MAIN FRONTEND
# ===============================

def main():
    root = tk.Tk()
    hook_tk(root)
    AsistenteGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
