"""Precipitação diária sobre o sítio: CHIRPS (1981-2025) e GPM IMERG V07 (2015-2025), via GEE.
Média da área do sítio (buffer 3 km, pois o CHIRPS tem pixel de ~5 km). Saída: dados/chuva_diaria.csv."""
import ee, pandas as pd
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[1]
ee.Initialize(project=__import__("os").environ.get("EE_PROJECT"))  # defina EE_PROJECT=<seu projeto GEE>
pt = ee.Geometry.Point([-45.4935, -23.6676]).buffer(3000)   # centro do sítio

def serie(colecao, banda, ini, fim, escala, nome):
    ic = ee.ImageCollection(colecao).filterDate(ini, fim).select(banda)
    def f(img):
        v = img.reduceRegion(ee.Reducer.mean(), pt, escala).get(banda)
        return ee.Feature(None, {"data": img.date().format("YYYY-MM-dd"), nome: v})
    fc = ic.map(f).filter(ee.Filter.notNull([nome]))
    # em blocos anuais para não estourar o limite
    return fc

linhas = []
for ano in range(1981, 2026):
    fc = serie("UCSB-CHG/CHIRPS/DAILY", "precipitation", f"{ano}-01-01", f"{ano+1}-01-01", 5566, "chirps")
    d = fc.getInfo()["features"]
    linhas += [(x["properties"]["data"], x["properties"]["chirps"]) for x in d]
    print(ano, len(d), flush=True)
df = pd.DataFrame(linhas, columns=["data", "chirps_mm"])
df.to_csv(RAIZ / "dados" / "chuva_chirps.csv", index=False)
