# ============================================================
# PRUEBA DE CLONACIÓN DE VOZ (no es el reel final)
# Insumo:    mi_voz.wav (muestra de tu voz, mono 24 kHz)
# Resultado: salidas/prueba_voz.wav (una frase generada con tu voz)
# ============================================================

from pathlib import Path

import numpy as np
import soundfile as sf
import torch
from faster_whisper import WhisperModel  # transcribe la muestra para obtener su texto
from qwen_tts import Qwen3TTSModel       # carga el modelo de voz Qwen3-TTS

RAIZ = Path(__file__).resolve().parent.parent
MUESTRA = RAIZ / "mi_voz.wav"
MODELO = RAIZ / "modelos" / "qwen3-tts-0.6b"
SALIDA = RAIZ / "salidas" / "prueba_voz.wav"
FRASE = "Hay cincuenta y seis incendios probables en Junín, pero no todos afectan a la misma cantidad de personas."

SALIDA.parent.mkdir(exist_ok=True)

# --- Paso 1: transcribir la muestra ---
# WhisperModel("base"): modelo pequeño de reconocimiento de voz; convierte audio en texto
# Antes: mi_voz.wav | Después: texto de lo que dijiste (necesario para clonar con texto de referencia)
whisper = WhisperModel("base", device="cpu", compute_type="int8")
segmentos, _ = whisper.transcribe(str(MUESTRA), language="es")
texto_muestra = " ".join(s.text.strip() for s in segmentos)
print("Texto de la muestra:", texto_muestra)

# --- Paso 2: cargar el modelo de voz en CPU ---
# from_pretrained: carga los pesos desde la carpeta local
# Antes: carpeta con archivos | Después: modelo listo en memoria
modelo = Qwen3TTSModel.from_pretrained(str(MODELO), device_map="cpu", torch_dtype=torch.float32)

# --- Paso 3: generar la frase con tu voz ---
# generate_voice_clone: produce audio con el timbre de la muestra
# Antes: texto nuevo | Después: lista de audios (y su frecuencia de muestreo)
audios, frecuencia = modelo.generate_voice_clone(
    text=FRASE,
    language="Spanish",
    ref_audio=str(MUESTRA),
    ref_text=texto_muestra,
)

# --- Paso 4: guardar y verificar ---
sf.write(SALIDA, np.asarray(audios[0]), frecuencia)
print("Guardado:", SALIDA, "| duración (s):", round(len(audios[0]) / frecuencia, 1))
