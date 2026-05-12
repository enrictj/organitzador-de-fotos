#  Organitzador de Galeria de Fotos i Vídeos

Script de Python que organitza automàticament fotos i vídeos en carpetes per **any** i **mes**, llegint les metadades reals dels fitxers (EXIF per a fotos, MP4/MOV per a vídeos) sense tocar els originals fins que ho confirmes.

---

##  Característiques

- Llegeix metadades **EXIF** de fotos (JPG, PNG, HEIC, TIFF, WEBP...)
- Llegeix metadades de **vídeos** MP4/MOV sense llibreries externes
- Fallback a **data de modificació** del fitxer si no hi ha metadades
- **Previsualització** de totes les operacions abans de confirmar
- Mode **còpia** (segur) o **moviment** (elimina originals)
- Resolució automàtica de **conflictes de nom** (afegeix `_1`, `_2`...)
- Noms de mesos en **català**
- Compatible amb **Google Takeout**

---

##  Instal·lació

**Instal·la les dependències:**

```bash
pip install pillow mutagen
```

---

##  Configuració

Abans d'executar l'script, edita les variables de configuració a la part superior del fitxer `organitza_galeria.py`:

```python
ORIGEN     = Path(r"C:\Users\Enric\Desktop\Galeria\2021")   # Carpeta amb les fotos originals
DESTI      = Path(r"C:\Users\Enric\Desktop\Galeria\2021_organitzat")  # On es crearan les carpetes
MODE       = "copiar"    # "copiar" (segur) o "moure" (elimina originals)
ESTRUCTURA = "any_mes"   # "any_mes" → 2021/01_Gener  |  "any_mes_dia" → 2021/01/15
```

| Variable | Valors possibles | Descripció |
|---|---|---|
| `ORIGEN` | Qualsevol ruta | Carpeta d'on llegeix les fotos/vídeos |
| `DESTI` | Qualsevol ruta | Carpeta on crearà l'estructura organitzada |
| `MODE` | `"copiar"` / `"moure"` | Còpia (segur) o mou els fitxers |
| `ESTRUCTURA` | `"any_mes"` / `"any_mes_dia"` | Nivell de detall de les carpetes |

---

##  Execució

Des del terminal (cmd, PowerShell, o terminal de Linux/Mac):

```bash
python organitza_galeria.py
```

L'script farà el següent:

**1.** Escanejarà la carpeta `ORIGEN` i trobarà totes les fotos i vídeos.

**2.** Mostrarà una previsualització de cada fitxer i on anirà:

```
────────────────────────────────────────────────────────────
  Organitzador de galeria  |  MODE: COPIAR
  Origen : C:\Users\Enric\Desktop\Galeria\2021
  Destí  : C:\Users\Enric\Desktop\Galeria\2021_organitzat
────────────────────────────────────────────────────────────

  153 fitxers trobats. Analitzant metadades...

  [          EXIF]  IMG_0042.jpg     →  2021/03_Març/IMG_0042.jpg
  [  MP4-metadata]  VID_0001.mp4     →  2021/07_Juliol/VID_0001.mp4
  [   data-fitxer]  foto_sense.jpg   →  2021/01_Gener/foto_sense.jpg
  ...
```

**3.** Demanarà confirmació:

```
  Copiar 153 fitxers a '...\2021_organitzat'? [s/N]
```

Escriu `s` i prem Enter per confirmar, o qualsevol altra tecla per cancel·lar.

**4.** Processarà els fitxers i mostrarà el resultat:

```
  [1/153] ✓ IMG_0042.jpg
  [2/153] ✓ VID_0001.mp4
  ...
  Fet! 153 fitxers processats correctament.
```

---


##  Extensions compatibles

**Fotos:** `.jpg` `.jpeg` `.png` `.heic` `.heif` `.tiff` `.tif` `.webp` `.bmp`

**Vídeos:** `.mp4` `.mov` `.avi` `.mkv` `.m4v` `.3gp` `.wmv` `.mts` `.m2ts`




## 📝 Llicència

MIT License — lliure per a ús personal i comercial.
