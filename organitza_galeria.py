"""
Organitzador de fotos i vídeos per data
========================================
Llegeix metadades EXIF (fotos) i MP4/MOV (vídeos) i organitza els fitxers
a carpetes Any/Mes sense moure els originals fins que ho confirmes.

Instal·lació de dependències (una sola vegada):
    pip install pillow mutagen

Ús:
    python organitza_galeria.py
"""

import os
import shutil
import struct
import sys
from datetime import datetime
from pathlib import Path

# ── Configuració ──────────────────────────────────────────────────────────────
ORIGEN      = Path(r"C:\Users\Enric\Desktop\Galeria\2021")
DESTI       = Path(r"C:\Users\Enric\Desktop\Galeria\2021_organitzat")
MODE        = "copiar"   # "copiar" (segur) o "moure" (elimina originals)
ESTRUCTURA  = "any_mes"  # "any_mes" → 2020/01_Gener  |  "any_mes_dia" → 2020/01/15
# ─────────────────────────────────────────────────────────────────────────────

EXTENSIONS_FOTO  = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".tiff", ".tif", ".webp", ".bmp"}
EXTENSIONS_VIDEO = {".mp4", ".mov", ".avi", ".mkv", ".m4v", ".3gp", ".wmv", ".mts", ".m2ts"}

MESOS_CA = ["Gener","Febrer","Març","Abril","Maig","Juny",
            "Juliol","Agost","Setembre","Octubre","Novembre","Desembre"]


# ── Lectura de metadades ───────────────────────────────────────────────────────

def data_exif_pillow(path: Path) -> datetime | None:
    """Llegeix DateTimeOriginal o DateTime via Pillow."""
    try:
        from PIL import Image
        from PIL.ExifTags import TAGS
        img = Image.open(path)
        exif = img._getexif()
        if not exif:
            return None
        for tag_id, val in exif.items():
            tag = TAGS.get(tag_id, "")
            if tag in ("DateTimeOriginal", "DateTime"):
                return datetime.strptime(val, "%Y:%m:%d %H:%M:%S")
    except Exception:
        pass
    return None


def data_exif_manual(path: Path) -> datetime | None:
    """Llegeix l'EXIF manualment (sense Pillow) per a fitxers JPEG."""
    try:
        with open(path, "rb") as f:
            data = f.read(65536)
        if data[:2] != b"\xff\xd8":
            return None
        i = 2
        while i < len(data) - 1:
            if data[i] != 0xFF:
                break
            marker = (data[i] << 8) | data[i+1]
            if marker == 0xFFE1:  # APP1 / EXIF
                if data[i+4:i+8] == b"Exif":
                    exif = data[i+10:]
                    little = exif[:2] == b"II"
                    def u16(o): return struct.unpack_from("<H" if little else ">H", exif, o)[0]
                    def u32(o): return struct.unpack_from("<I" if little else ">I", exif, o)[0]
                    ifd = u32(4)
                    n   = u16(ifd)
                    for e in range(n):
                        off  = ifd + 2 + e * 12
                        tag  = u16(off)
                        if tag in (0x9003, 0x0132):  # DateTimeOriginal / DateTime
                            voff = u32(off + 8)
                            raw  = exif[voff:voff+19].decode("ascii", errors="ignore")
                            if len(raw) >= 19:
                                return datetime.strptime(raw, "%Y:%m:%d %H:%M:%S")
            if marker == 0xFFDA:
                break
            seg_len = (data[i+2] << 8) | data[i+3]
            i += 2 + seg_len
    except Exception:
        pass
    return None


def data_video_mp4(path: Path) -> datetime | None:
    """Llegeix la data de creació d'un vídeo MP4/MOV/M4V."""
    try:
        with open(path, "rb") as f:
            raw = f.read(8 * 1024 * 1024)  # primers 8 MB
        i = 0
        while i < len(raw) - 8:
            box_size = struct.unpack_from(">I", raw, i)[0]
            box_type = raw[i+4:i+8]
            if box_size < 8:
                break
            if box_type in (b"moov", b"udta", b"meta", b"trak", b"mdia", b"minf", b"stbl"):
                i += 8
                continue
            if box_type in (b"mvhd", b"tkhd"):
                version = raw[i+8]
                if version == 1:
                    ts = struct.unpack_from(">Q", raw, i+16)[0]
                else:
                    ts = struct.unpack_from(">I", raw, i+12)[0]
                # L'epoch MP4 comença l'1 de gener de 1904
                epoch = datetime(1904, 1, 1)
                try:
                    dt = epoch.fromtimestamp((epoch - datetime(1970,1,1)).total_seconds() * -1 + ts)
                    # Càlcul correcte
                    import calendar
                    offset = calendar.timegm((1904, 1, 1, 0, 0, 0)) * -1
                    unix_ts = ts - offset - (70 * 365 + 17) * 86400
                    if 0 < unix_ts < 4_000_000_000:
                        return datetime.utcfromtimestamp(unix_ts)
                except Exception:
                    pass
            i += box_size
    except Exception:
        pass

    # Fallback: mutagen
    try:
        from mutagen.mp4 import MP4
        tags = MP4(path).tags
        if tags and "\xa9day" in tags:
            raw_date = tags["\xa9day"][0]
            for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%Y"):
                try:
                    return datetime.strptime(raw_date[:len(fmt)], fmt)
                except ValueError:
                    continue
    except Exception:
        pass
    return None


def data_fitxer(path: Path) -> datetime:
    """Última alternativa: data de modificació del fitxer."""
    return datetime.fromtimestamp(path.stat().st_mtime)


def obtenir_data(path: Path) -> tuple[datetime, str]:
    """Retorna (data, font) per a qualsevol fitxer suportat."""
    ext = path.suffix.lower()
    if ext in EXTENSIONS_FOTO:
        dt = data_exif_pillow(path) or data_exif_manual(path)
        if dt:
            return dt, "EXIF"
    if ext in EXTENSIONS_VIDEO:
        dt = data_video_mp4(path)
        if dt:
            return dt, "MP4-metadata"
    dt = data_fitxer(path)
    return dt, "data-fitxer"


# ── Construcció de la ruta destí ──────────────────────────────────────────────

def ruta_desti(dt: datetime, nom: str) -> Path:
    mes_num  = f"{dt.month:02d}"
    mes_nom  = MESOS_CA[dt.month - 1]
    if ESTRUCTURA == "any_mes":
        subcarpeta = Path(str(dt.year)) / f"{mes_num}_{mes_nom}"
    else:  # any_mes_dia
        subcarpeta = Path(str(dt.year)) / mes_num / f"{dt.day:02d}"
    return DESTI / subcarpeta / nom


# ── Resolució de conflictes de nom ────────────────────────────────────────────

def nom_unic(path: Path) -> Path:
    if not path.exists():
        return path
    stem, suffix = path.stem, path.suffix
    i = 1
    while True:
        nou = path.with_name(f"{stem}_{i}{suffix}")
        if not nou.exists():
            return nou
        i += 1


# ── Programa principal ────────────────────────────────────────────────────────

def main():
    totes_extensions = EXTENSIONS_FOTO | EXTENSIONS_VIDEO
    fitxers = [p for p in ORIGEN.rglob("*")
               if p.is_file() and p.suffix.lower() in totes_extensions]

    if not fitxers:
        print(f"No s'han trobat fotos ni vídeos a: {ORIGEN}")
        sys.exit(0)

    print(f"\n{'─'*60}")
    print(f"  Organitzador de galeria  |  MODE: {MODE.upper()}")
    print(f"  Origen : {ORIGEN}")
    print(f"  Destí  : {DESTI}")
    print(f"{'─'*60}\n")
    print(f"  {len(fitxers)} fitxers trobats. Analitzant metadades...\n")

    operacions = []
    stats = {"EXIF": 0, "MP4-metadata": 0, "data-fitxer": 0}

    for path in sorted(fitxers):
        dt, font = obtenir_data(path)
        dest = nom_unic(ruta_desti(dt, path.name))
        stats[font] += 1
        operacions.append((path, dest, font, dt))
        print(f"  [{font:>13}]  {path.name:<40}  →  {dest.relative_to(DESTI)}")

    print(f"\n{'─'*60}")
    print(f"  Resum de fonts de data:")
    for font, n in stats.items():
        if n:
            print(f"    {font:<15} {n} fitxers")
    print(f"{'─'*60}\n")

    accio = "Copiar" if MODE == "copiar" else "Moure"
    resposta = input(f"  {accio} {len(operacions)} fitxers a '{DESTI}'? [s/N] ").strip().lower()
    if resposta != "s":
        print("  Operació cancel·lada.")
        sys.exit(0)

    errors = 0
    for i, (origen, dest, font, dt) in enumerate(operacions, 1):
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            if MODE == "copiar":
                shutil.copy2(origen, dest)
            else:
                shutil.move(str(origen), dest)
            print(f"  [{i}/{len(operacions)}] ✓ {origen.name}")
        except Exception as e:
            print(f"  [{i}/{len(operacions)}] ✗ {origen.name}  →  {e}")
            errors += 1

    print(f"\n  {'─'*50}")
    print(f"  Fet! {len(operacions) - errors} fitxers processats correctament.")
    if errors:
        print(f"  {errors} errors.")
    print()


if __name__ == "__main__":
    main()