"""Baixa as duas cenas Sentinel-2 SR (seca e chuvosa) do GEE, recortadas em janela de 8 km x 8 km em SIRGAS 2000 UTM 23S, 10 m.
Bandas: B2,B3,B4,B8,B11,SCL (+ JRC GSW 'occurrence' como referência independente de água superficial)."""
import ee, requests, io, sys
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[1]
ee.Initialize(project=__import__("os").environ.get("EE_PROJECT"))  # defina EE_PROJECT=<seu projeto GEE>
CENAS = {"seca": "20240823T131241_20240823T131319_T23KMP", "chuvosa": "20240331T131239_20240331T131627_T23KMP"}
X, Y = 449689.0, 7382485.0; R = 4000
reg = ee.Geometry.Rectangle([X-R, Y-R, X+R, Y+R], proj="EPSG:31983", geodesic=False)
for nome, sid in CENAS.items():
    img = ee.Image("COPERNICUS/S2_SR_HARMONIZED/" + sid).select(["B2","B3","B4","B8","B11","SCL"])
    url = img.getDownloadURL({"region": reg, "crs": "EPSG:31983", "scale": 10, "format": "GEO_TIFF"})
    r = requests.get(url, timeout=300); r.raise_for_status()
    (RAIZ/"dados"/f"s2_{nome}.tif").write_bytes(r.content); print(nome, len(r.content))
gsw = ee.Image("JRC/GSW1_4/GlobalSurfaceWater").select(["occurrence", "seasonality"]).unmask(0)
url = gsw.getDownloadURL({"region": reg, "crs": "EPSG:31983", "scale": 30, "format": "GEO_TIFF"})
(RAIZ/"dados"/"jrc_gsw.tif").write_bytes(requests.get(url, timeout=300).content); print("gsw ok")
