# ============================================================
# REEL: del guion revisado a un video vertical narrado con tu voz
# Insumo:    salidas/guion.json y mi_voz.wav
# Resultado: salidas/reel.mp4, salidas/reel.srt y salidas/narracion.wav
# ============================================================

import json
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
from faster_whisper import WhisperModel
from PIL import Image, ImageDraw, ImageFont, ImageOps
from qwen_tts import Qwen3TTSModel
import imageio_ffmpeg

RAIZ = Path(__file__).resolve().parent.parent
MUESTRA = RAIZ / "mi_voz.wav"
MODELO = RAIZ / "modelos" / "qwen3-tts-0.6b"
SALIDAS = RAIZ / "salidas"
PAUSA_S = 0.4          # silencio entre escenas, en segundos
ANCHO, ALTO = 1080, 1920
FPS = 30
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

FUENTE_NEGRITA = "C:/Windows/Fonts/arialbd.ttf"
FUENTE_NORMAL = "C:/Windows/Fonts/arial.ttf"


# PROCESO 1: texto de la muestra (para clonar la voz)
# Insumo:    mi_voz.wav
# Resultado: salidas/muestra_texto.txt (lo que dijiste en la muestra)
def texto_de_la_muestra():
    ruta = SALIDAS / "muestra_texto.txt"
    if ruta.exists():
        return ruta.read_text(encoding="utf-8")
    whisper = WhisperModel("base", device="cpu", compute_type="int8")
    segmentos, _ = whisper.transcribe(str(MUESTRA), language="es")
    texto = " ".join(s.text.strip() for s in segmentos)
    ruta.write_text(texto, encoding="utf-8")
    return texto


# PROCESO 2: narrar cada escena con tu voz
# Insumo:    guion.json (frase de cada escena)
# Resultado: una lista de audios, uno por escena, con sus duraciones
def recortar_silencios(audio, frecuencia, umbral=0.01, pausa_max_s=0.35):
    # Quita el silencio al inicio y al final, y reduce las pausas internas a un máximo de 0.35 s
    # Antes: audio con silencios largos de hasta varios segundos | Después: solo voz y pausas cortas
    ventana = int(0.03 * frecuencia)
    energia = np.sqrt(np.convolve(audio**2, np.ones(ventana) / ventana, mode="same"))
    hay_voz = energia > umbral
    cambios = np.flatnonzero(np.diff(hay_voz.astype(int))) + 1
    limites = np.concatenate([[0], cambios, [len(hay_voz)]])
    partes = []
    for inicio, fin in zip(limites[:-1], limites[1:]):
        if hay_voz[inicio]:
            partes.append(audio[inicio:fin])
        elif inicio > 0 and fin < len(hay_voz):  # silencio entre palabras: se acorta
            partes.append(np.zeros(min(fin - inicio, int(pausa_max_s * frecuencia)), dtype=audio.dtype))
    return np.concatenate(partes)


def narrar_escenas(escenas, texto_muestra):
    modelo = Qwen3TTSModel.from_pretrained(str(MODELO), device_map="cpu", dtype=torch.float32)
    audios = []
    for i, escena in enumerate(escenas, start=1):
        print(f"Narrando escena {i}/{len(escenas)}...")
        # Duración esperada: unos 0.6 s por palabra, más 4 s de margen
        limite_s = 4 + 0.6 * len(escena["frase"].split())
        mejor = None
        for intento in range(1, 4):
            wavs, frecuencia = modelo.generate_voice_clone(
                text=escena["frase"],
                language="Spanish",
                ref_audio=str(MUESTRA),
                ref_text=texto_muestra,
            )
            audio = recortar_silencios(np.asarray(wavs[0], dtype=np.float32), frecuencia)
            duracion = len(audio) / frecuencia
            print(f"  intento {intento}: {duracion:.1f} s (límite {limite_s:.1f} s)")
            if mejor is None or duracion < len(mejor) / frecuencia:
                mejor = audio
            if duracion <= limite_s:
                break
        audios.append(mejor)
    return audios, frecuencia


# PROCESO 3: dibujar un cuadro vertical por escena
# Insumo:    cada escena (cifra, etiqueta y frase)
# Resultado: salidas/cuadros/escena_N.png, de 1080 x 1920 px
def dibujar_cuadros(escenas):
    carpeta = SALIDAS / "cuadros"
    carpeta.mkdir(exist_ok=True)
    f_cifra = ImageFont.truetype(FUENTE_NEGRITA, 260)
    f_etiqueta = ImageFont.truetype(FUENTE_NEGRITA, 64)
    f_frase = ImageFont.truetype(FUENTE_NORMAL, 52)
    f_pie = ImageFont.truetype(FUENTE_NORMAL, 36)
    rutas = []
    for i, escena in enumerate(escenas, start=1):
        img = Image.new("RGB", (ANCHO, ALTO), (28, 26, 23))
        d = ImageDraw.Draw(img)
        d.text((80, 300), escena["etiqueta"], font=f_etiqueta, fill=(240, 138, 75))
        d.text((80, 520), escena["cifra"], font=f_cifra, fill=(247, 243, 236))
        # Imagen del proyecto de incendios (mapa), recortada al contenido y centrada en el área 840-1340
        if "imagen" in escena:
            origen = RAIZ.parent / "incendios-2026" / "salidas" / escena["imagen"]
            mapa = Image.open(origen).convert("RGB")
            mapa = mapa.crop(ImageOps.invert(mapa).getbbox())
            mapa.thumbnail((920, 500))
            img.paste(mapa, (80 + (920 - mapa.width) // 2, 840 + (500 - mapa.height) // 2))
        # Barra que muestra qué parte del total representa la cifra (proporción de 0 a 1)
        if "proporcion" in escena:
            d.rectangle([80, 900, 1000, 1000], fill=(60, 56, 50))
            d.rectangle([80, 900, 80 + int(920 * escena["proporcion"]), 1000], fill=(240, 138, 75))
        # Frase como subtítulo en la parte baja; si son más de cuatro líneas, se usa letra más chica
        def partir(fuente):
            lineas, actual = [], ""
            for palabra in escena["frase"].split():
                prueba = (actual + " " + palabra).strip()
                if d.textlength(prueba, font=fuente) > ANCHO - 160:
                    lineas.append(actual)
                    actual = palabra
                else:
                    actual = prueba
            lineas.append(actual)
            return lineas

        lineas = partir(f_frase)
        paso = 70
        if len(lineas) > 4:
            f_frase = ImageFont.truetype(FUENTE_NORMAL, 44)
            lineas = partir(f_frase)
            paso = 58
        y = 1400
        for linea in lineas:
            d.text((80, y), linea, font=f_frase, fill=(247, 243, 236))
            y += paso
        d.text((80, ALTO - 120), "Voz generada con IA", font=f_pie, fill=(217, 207, 193))
        ruta = carpeta / f"escena_{i}.png"
        img.save(ruta)
        rutas.append(ruta)
    return rutas


# PROCESO 4: unir narración, cuadros y subtítulos en un solo video
# Insumo:    audios por escena y cuadros PNG
# Resultado: salidas/reel.mp4, salidas/narracion.wav y salidas/reel.srt
def armar_video(escenas, audios, frecuencia, rutas):
    # Cada escena dura lo que dura su audio, más una pausa
    duraciones = [len(a) / frecuencia + PAUSA_S for a in audios]

    # Narración completa: audio de cada escena con silencio entre ellas
    silencio = np.zeros(int(PAUSA_S * frecuencia), dtype=np.float32)
    narracion = np.concatenate([np.concatenate([a, silencio]) for a in audios])
    sf.write(SALIDAS / "narracion.wav", narracion, frecuencia)

    # Video: un segmento por escena (cuadro fijo durante su duración) y luego se pega
    segmentos = []
    for i, (ruta, dur) in enumerate(zip(rutas, duraciones), start=1):
        seg = SALIDAS / "cuadros" / f"segmento_{i}.mp4"
        subprocess.run([
            FFMPEG, "-y", "-loop", "1", "-i", str(ruta), "-t", f"{dur:.3f}",
            "-r", str(FPS), "-c:v", "libx264", "-pix_fmt", "yuv420p", str(seg),
        ], check=True, capture_output=True)
        segmentos.append(seg)

    lista = SALIDAS / "cuadros" / "lista.txt"
    lista.write_text("".join(f"file '{s.as_posix()}'\n" for s in segmentos), encoding="utf-8")
    sin_audio = SALIDAS / "cuadros" / "sin_audio.mp4"
    subprocess.run([FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", str(lista), "-c", "copy", str(sin_audio)],
                   check=True, capture_output=True)
    subprocess.run([
        FFMPEG, "-y", "-i", str(sin_audio), "-i", str(SALIDAS / "narracion.wav"),
        "-c:v", "copy", "-c:a", "aac", "-shortest", str(SALIDAS / "reel.mp4"),
    ], check=True, capture_output=True)

    # Subtítulos en formato SRT: una entrada por escena
    def tiempo(segundos):
        h, resto = divmod(int(segundos), 3600)
        m, s = divmod(resto, 60)
        ms = int((segundos - int(segundos)) * 1000)
        return f"{h:02}:{m:02}:{s:02},{ms:03}"

    bloques, inicio = [], 0.0
    for i, (escena, dur) in enumerate(zip(escenas, duraciones), start=1):
        fin = inicio + dur - PAUSA_S
        bloques.append(f"{i}\n{tiempo(inicio)} --> {tiempo(fin)}\n{escena['frase']}\n")
        inicio += dur
    (SALIDAS / "reel.srt").write_text("\n".join(bloques), encoding="utf-8")

    total = sum(duraciones)
    print(f"Video: salidas/reel.mp4 | duración aproximada: {total:.1f} s")


if __name__ == "__main__":
    SALIDAS.mkdir(exist_ok=True)
    escenas = json.loads((SALIDAS / "guion.json").read_text(encoding="utf-8"))
    texto_muestra = texto_de_la_muestra()
    audios, frecuencia = narrar_escenas(escenas, texto_muestra)
    rutas = dibujar_cuadros(escenas)
    armar_video(escenas, audios, frecuencia, rutas)
