"""Sítio de Caraguatatuba (área capaz de receber um aeroporto regional) e recorte da hidrografia FBDS.

Parâmetros copiados de C:/Projetos/Tese/apps/m4_encaixe/referencias.py (centro em SIRGAS 2000 UTM 23S,
rumo em graus do norte, sentido horário; polígono de 3.625 m x 610 m; incerteza de posição ~250 m).
"""
import json, sys
from pathlib import Path
import numpy as np, geopandas as gpd
from shapely.geometry import Polygon, box

RAIZ = Path(__file__).resolve().parents[1]
DADOS = RAIZ / "dados"; DADOS.mkdir(exist_ok=True)
FBDS = Path(r"C:\Projetos\Tese\dados\m3_exclusao\brutos\caraguatatuba\fbds_hidro_principal.geojson")
X, Y, RUMO, L, W = 449689.0, 7382485.0, 103.0, 3625.0, 610.0
CRS = 31983

a = np.deg2rad(RUMO)
eu = np.array([np.sin(a), np.cos(a)]); ev = np.array([np.cos(a), -np.sin(a)])
c = np.array([X, Y])
poly = Polygon([c + u * eu + v * ev for u, v in ((-L/2, -W/2), (L/2, -W/2), (L/2, W/2), (-L/2, W/2))])
g = gpd.GeoDataFrame({"nome": ["sitio_caraguatatuba"]}, geometry=[poly], crs=CRS)
g.to_file(DADOS / "sitio.geojson", driver="GeoJSON")
g.to_crs(4326).to_file(DADOS / "sitio_wgs84.geojson", driver="GeoJSON")
print("área do sítio (km²):", poly.area / 1e6, "bounds WGS84:", g.to_crs(4326).total_bounds)

# hidrografia FBDS recortada a 3 km do sítio
jan = poly.buffer(3000)
h = gpd.read_file(FBDS, bbox=tuple(gpd.GeoSeries([jan], crs=CRS).to_crs(4326).total_bounds))
print(h.columns.tolist(), len(h), h.geometry.geom_type.value_counts().to_dict())
h = h.to_crs(CRS)
h = h[h.intersects(jan)]
h.to_file(DADOS / "fbds_recorte.gpkg", driver="GPKG")
print("recorte:", len(h))
