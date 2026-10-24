# ============================================================
# GUION DEL REEL: del README del proyecto a un guion con escenas
# Insumo:    README.md del proyecto de incendios (fuente)
# Resultado: salidas/prompt.txt (para pegar en Qwen) y
#            salidas/guion.json (escenas revisadas contra el README)
# ============================================================

import argparse
import json
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FUENTE = RAIZ.parent / "incendios-2026" / "README.md"  # README del proyecto de incendios
SALIDAS = RAIZ / "salidas"

INSTRUCCIONES = """Eres guionista de un reel de 45 a 55 segundos en español sobre el texto que sigue.
Devuelve SOLO un arreglo JSON de 6 escenas. Cada escena tiene tres campos:
- "frase": lo que se narra, en 15 a 25 palabras. Escribe los números en palabras.
- "cifra": el número que se muestra en pantalla, tal como aparece en el texto (ej. "746.046" o "69 %").
- "etiqueta": qué mide esa cifra, en 3 a 6 palabras.
Reglas: usa solo datos que aparezcan en el texto; no agregues cifras, fechas ni causas; no digas "en tiempo real".
Incluye en la última escena que es una evaluación inicial y que cercanía no es lo mismo que daño.

TEXTO FUENTE:
"""


# PROCESO 1: generar el prompt para pegar en el chat de Qwen
# Insumo:    README.md del proyecto de incendios
# Resultado: salidas/prompt.txt (instrucciones + texto completo)
def preparar_prompt():
    texto = FUENTE.read_text(encoding="utf-8")
    SALIDAS.mkdir(exist_ok=True)
    ruta = SALIDAS / "prompt.txt"
    ruta.write_text(INSTRUCCIONES + texto, encoding="utf-8")
    print("Prompt guardado en:", ruta, "| palabras:", len(texto.split()))
    print("Pégalo en chat.qwen.ai, copia la respuesta JSON y guárdala en salidas/respuesta.txt")


# PROCESO 2: revisar la respuesta de Qwen contra el README
# Insumo:    salidas/respuesta.txt (JSON que devolvió Qwen)
# Resultado: salidas/guion.json y una lista de cifras que NO aparecen en el README
def normalizar_cifra(texto):
    # Deja solo los dígitos, para comparar "746.046" con "746,046" y "5 km" con "5"
    return re.sub(r"\D", "", texto)


def revisar_respuesta():
    texto_fuente = FUENTE.read_text(encoding="utf-8")
    cifras_fuente = {normalizar_cifra(c) for c in re.findall(r"\d[\d.,]*", texto_fuente)}

    respuesta = (SALIDAS / "respuesta.txt").read_text(encoding="utf-8")
    # Busca el arreglo JSON dentro de la respuesta (Qwen a veces agrega texto alrededor)
    inicio, fin = respuesta.find("["), respuesta.rfind("]")
    escenas = json.loads(respuesta[inicio : fin + 1])

    sin_respaldo = []
    for i, escena in enumerate(escenas, start=1):
        cifra = normalizar_cifra(escena["cifra"])
        if cifra not in cifras_fuente:
            sin_respaldo.append((i, escena["cifra"]))

    (SALIDAS / "guion.json").write_text(json.dumps(escenas, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Escenas: {len(escenas)} | guardadas en salidas/guion.json")
    if sin_respaldo:
        print("REVISAR: estas cifras no aparecen en el README:")
        for numero, cifra in sin_respaldo:
            print(f"  escena {numero}: {cifra}")
    else:
        print("OK: todas las cifras aparecen en el README. Falta revisar las frases a mano.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--respuesta", action="store_true", help="revisar salidas/respuesta.txt")
    args = parser.parse_args()
    if args.respuesta:
        revisar_respuesta()
    else:
        preparar_prompt()
