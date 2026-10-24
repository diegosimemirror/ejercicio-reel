# ejercicio-reel · ¿A quién afecta el fuego en Junín?

Reel de 39 segundos, narrado con mi voz clonada (Qwen3-TTS 0.6B, en CPU), a partir del README del proyecto de incendios de Junín.

**Texto que usé:** README de `incendios-2026` (Junín, camino D): focos de calor del 14 al 21 de octubre de 2026, criterios de evidencia, población a 5 km y red de salud (RENIPRESS, DIRESA y EsSalud).

**Página del proyecto:** https://claude.ai/artifact/2fVRwcStbC5LgvMmfuYn8h

## Archivos

- `salidas/reel.mp4`: el reel vertical (1080 × 1920), con mapas y barras.
- `salidas/reel.srt`: subtítulos, una entrada por escena.
- `salidas/posts.md`: tres posts (LinkedIn, Facebook y X), cada uno con el aviso de voz generada con IA.
- `salidas/portada.png`: primer cuadro del reel.
- `salidas/guion.json`: el guion final, con sus cifras.
- `salidas/respuesta.txt` y `salidas/prompt.txt`: el texto que se usó para generar y revisar el guion.
- `scripts/guion.py`: revisa que cada cifra del guion aparezca en el README.
- `scripts/hacer_reel.py`: narra cada escena, dibuja los cuadros y arma el video.

## Qué corregí del guion

1. **Quién escribió el guion:** lo escribí yo, a partir del README; no lo generó Qwen. Lo verifiqué con `scripts/guion.py`, que compara cada cifra con el README.
2. **Cifras que no estaban en el README:** en el texto que traje de la clase, había cifras que no aparecían en el README: unas 2,000 ha, 268 mil personas con tres o más focos, 192 mil personas, 117 establecimientos, 11 distritos y "15 segundos" de actualización. No las usé. Usé 1,958 ha para Río Tambo, que sí aparece en el README.
3. **Términos sin explicar:** "foco" pasó a "alerta del satélite" o "punto de calor"; "criterios de evidencia" se explica como "solo los que probablemente son incendios"; "crítico" se explica como centro sin 4G garantizado con hospital a más de dos horas.
4. **"Señal" ambigua:** la escena dice "cobertura 4G garantizada, es decir, internet móvil para una teleconsulta".
5. **Escena sobre personas que "cuenta" un foco:** se cambió por "queda a cinco kilómetros de casi trescientas mil personas".
6. **Escena de 68,392 personas cerca de incendios activos:** se quitó, porque era secundaria.
7. **Escenas de la red de salud:** se agregaron (centros críticos en el valle del Ene y cobertura 4G), porque son uno de los aportes propios del proyecto.
8. **Última frase** ("Estar cerca del fuego no significa estar dañado..."): se retiró por poco clara.
9. **Duración:** la primera versión duraba 64 segundos, y luego 74. Recorté los silencios que el modelo de voz insertaba entre frases, y el reel quedó en 39 segundos.

## Aviso

La voz es generada con IA (clonación de mi voz con Qwen3-TTS). La muestra de voz no está en el repositorio.
