# app/main.py
import os
import re
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Tuple
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from PIL import Image, ExifTags

def _env_list(key: str, default: str = ""):
    raw = os.environ.get(key, default)
    return [x.strip() for x in raw.split(",") if x.strip()]

# === CONFIG via ENV ===
# IMPORTANT: dins del contenidor muntarem el SYMLINK a /data/fotos_immich
# i aquí apuntem a la subcarpeta 'admin'
FOTOS_ROOT = Path(os.environ.get("FOTOS_ROOT", "/data/fotos_immich/admin"))
CORS_ORIGINS = _env_list("CORS_ALLOW_ORIGINS", "http://localhost:8088,http://192.168.1.10:8088")
# ======================

app = FastAPI(title="Photos API (Filesystem mode)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

if not FOTOS_ROOT.exists():
    raise RuntimeError(f"No trobo la carpeta de fotos: {FOTOS_ROOT}")

# Expose /media/admin/<ANY>/<YYYY-MM-DD>/<fitxer>
app.mount("/media", StaticFiles(directory=str(FOTOS_ROOT.parent), html=False), name="media")

def _exif_to_deg(v) -> Optional[float]:
    try:
        d = float(v[0][0]) / float(v[0][1])
        m = float(v[1][0]) / float(v[1][1])
        s = float(v[2][0]) / float(v[2][1])
        return d + (m/60.0) + (s/3600.0)
    except Exception:
        return None

def _gps_from_exif(img: Path) -> Tuple[Optional[float], Optional[float]]:
    try:
        with Image.open(img) as im:
            exif = im._getexif()
            if not exif: return None, None
            tags = {ExifTags.TAGS.get(k,k): v for k,v in exif.items() if k in ExifTags.TAGS}
            gps  = tags.get("GPSInfo")
            if not gps: return None, None
            gmap = {ExifTags.GPSTAGS.get(k,k): v for k,v in gps.items()}
            lat = _exif_to_deg(gmap.get("GPSLatitude")) if gmap.get("GPSLatitude") else None
            lon = _exif_to_deg(gmap.get("GPSLongitude")) if gmap.get("GPSLongitude") else None
            if lat is not None and gmap.get("GPSLatitudeRef") in ("S","s"): lat = -lat
            if lon is not None and gmap.get("GPSLongitudeRef") in ("W","w"): lon = -lon
            return lat, lon
    except Exception:
        return None, None

def _gps_from_xmp(img: Path) -> Tuple[Optional[float], Optional[float]]:
    """
    Busca un sidecar .xmp (por ejemplo perro.webp.xmp)
    y extrae <exif:GPSLatitude> y <exif:GPSLongitude> si existen.
    Formato típico: 38,32.88992538N   /   2,48.75W
    """
    xmp_path = img.with_suffix(img.suffix + ".xmp")  # perro.webp -> perro.webp.xmp
    if not xmp_path.exists():
        return None, None

    try:
        text = xmp_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None, None

    lat_match = re.search(r"<exif:GPSLatitude>([^<]+)</exif:GPSLatitude>", text)
    lon_match = re.search(r"<exif:GPSLongitude>([^<]+)</exif:GPSLongitude>", text)
    if not lat_match or not lon_match:
        return None, None

    def parse_coord(raw: str) -> Optional[float]:
        raw = raw.strip()
        # Esperamos cosas tipo "38,32.88992538N" o "2,48.75W"
        m = re.match(r"^\s*(\d+),([\d\.]+)\s*([NnSsEeWw])\s*$", raw)
        if not m:
            return None
        deg = float(m.group(1))
        minutes = float(m.group(2))
        hemi = m.group(3)
        value = deg + minutes / 60.0
        if hemi in ("S", "s", "W", "w"):
            value = -value
        return value

    lat = parse_coord(lat_match.group(1))
    lon = parse_coord(lon_match.group(1))
    return lat, lon


def _gps_from_anywhere(img: Path) -> Tuple[Optional[float], Optional[float]]:
    # 1) Intentar EXIF
    lat, lon = _gps_from_exif(img)
    if lat is not None and lon is not None:
        return lat, lon

    # 2) Intentar XMP
    return _gps_from_xmp(img)


def _list_images_for_date(date_str: str) -> List[Path]:
    try:
        d = datetime.fromisoformat(date_str).date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Format: YYYY-MM-DD")
    day_dir = FOTOS_ROOT / f"{d.year}" / date_str
    if not day_dir.exists(): return []
    imgs: List[Path] = []
    for ext in ("*.jpg","*.avif","*.jpeg","*.png","*.webp","*.JPG","*.JPEG","*.PNG","*.WEBP"):
        imgs.extend(day_dir.glob(ext))
    return sorted(imgs)

@app.get("/health")
def health(): return {"ok": True}

@app.get("/photos")
def list_photos(date: str = Query(..., pattern=r"^\d{4}-\d{2}-\d{2}$")):
    files = _list_images_for_date(date)
    items = []
    for p in files:
        lat, lon = _gps_from_anywhere(p)
        items.append({
            "id": p.stem,
            "takenAt": None,
            "lat": lat, "lon": lon,
            "thumb": f"/media/admin/{p.parent.parent.name}/{p.parent.name}/{p.name}",
            "full":  f"/media/admin/{p.parent.parent.name}/{p.parent.name}/{p.name}",
        })
    return {"date": date, "count": len(items), "items": items}
