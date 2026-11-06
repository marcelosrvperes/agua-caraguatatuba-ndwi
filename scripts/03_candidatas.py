"""Lista as cenas Sentinel-2 SR (2018-2025) sobre o sítio com fração de nuvem/sombra no entorno (SCL) e a chuva
antecedente (CHIRPS 3, 7 e 30 dias). Saída: dados/candidatas_s2.csv."""
import ee, pandas as pd
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[1]
ee.Initialize(project=__import__("os").environ.get("EE_PROJECT"))  # defina EE_PROJECT=<seu projeto GEE>
sitio = ee.Geometry.Point([-45.4935, -23.6676])
area = sitio.buffer(2500)           # sítio + entorno para avaliar nuvem
ic = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterBounds(sitio)
      .filterDate("2018-01-01", "2026-01-01").filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 70)))
def f(img):
    scl = img.select("SCL")
    ruim = scl.eq(3).Or(scl.eq(8)).Or(scl.eq(9)).Or(scl.eq(10)).Or(scl.eq(1)).Or(scl.eq(0))
    fr = ruim.reduceRegion(ee.Reducer.mean(), area, 20).get("SCL")
    return ee.Feature(None, {"id": img.get("system:index"), "data": img.date().format("YYYY-MM-dd"),
                             "ruim": fr, "tile": img.get("MGRS_TILE")})
res = ic.map(f).getInfo()["features"]
df = pd.DataFrame([r["properties"] for r in res]).dropna()
ch = pd.read_csv(RAIZ / "dados" / "chuva_chirps.csv", parse_dates=["data"]).set_index("data").chirps_mm
df["data"] = pd.to_datetime(df["data"])
for n in (3, 7, 30):
    df[f"p{n}"] = [ch[d - pd.Timedelta(days=n):d - pd.Timedelta(days=1)].sum() for d in df["data"]]
df.sort_values("data").to_csv(RAIZ / "dados" / "candidatas_s2.csv", index=False)
print(len(df)); print(df[df.ruim < 0.02].sort_values("data").to_string())

# Regra de escolha (aplicada a mão em 04_baixar_s2.py): ruim < 1%; seca = menor p30 em jun-set; chuvosa = maior p7 em dez-mar; mesmo ano.
d = df[df.ruim < 0.01].copy(); d["m"] = d["data"].dt.month; d["ano"] = d["data"].dt.year
for a, g in d.groupby("ano"):
    print("regra", a, g[g.m.between(6, 9)].nsmallest(1, "p30")["data"].dt.date.tolist(), g[g.m.isin([12, 1, 2, 3])].nlargest(1, "p7")["data"].dt.date.tolist())
