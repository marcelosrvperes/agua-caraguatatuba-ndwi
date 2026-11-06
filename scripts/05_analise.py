"""Análise e figuras do artigo. Entradas: dados/chuva_chirps.csv, dados/s2_*.tif, dados/jrc_gsw.tif, dados/sitio.geojson,
dados/fbds_recorte.gpkg. Saídas: dados/resultados.json, figuras/fig_precip.pdf, figuras/fig_ndwi.pdf."""
import json
from pathlib import Path

import geopandas as gpd
import matplotlib
import numpy as np
import pandas as pd
import rasterio
from rasterio.features import rasterize
from skimage.filters import threshold_otsu

matplotlib.use("Agg")
import matplotlib.patches as mp
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm

RAIZ = Path(__file__).resolve().parents[1]
D = RAIZ / "dados"
F = RAIZ / "figuras"
F.mkdir(exist_ok=True)
plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif"],
                     "font.size": 8, "axes.linewidth": .6})
R = {}
DATAS = {"seca": "2024-08-23", "chuvosa": "2024-03-31"}

# ---------- precipitação ----------
ch = pd.read_csv(D / "chuva_chirps.csv", parse_dates=["data"]).set_index("data").chirps_mm
mes = ch.resample("MS").sum()
clim = mes.groupby(mes.index.month).agg(["mean", "std"])
anual = mes.groupby(mes.index.year).sum()
media_mes = anual.mean() / 12
seca_m = [m for m in range(1, 13) if clim.loc[m, "mean"] < media_mes]
R["chuva"] = {"periodo": [str(ch.index.min().date()), str(ch.index.max().date())],
              "anual_mm": round(anual.mean()), "anual_dp": round(anual.std()),
              "media_mensal_mm": round(media_mes), "meses_secos": seca_m,
              "clim_mensal": {int(k): round(float(v)) for k, v in clim["mean"].items()},
              "seca_total_mm": round(clim.loc[seca_m, "mean"].sum()),
              "chuvosa_total_mm": round(clim.drop(seca_m)["mean"].sum()),
              "ano2024_mm": round(anual[2024]), "mensal2024": [round(float(z)) for z in mes["2024"].values]}
for n, d in DATAS.items():
    t = pd.Timestamp(d)
    R["chuva"][n] = {"data": d}
    for k in (3, 7, 30):
        R["chuva"][n][f"p{k}"] = round(float(ch[t - pd.Timedelta(days=k):t - pd.Timedelta(days=1)].sum()), 1)
    R["chuva"][n]["mes_mm"] = round(float(mes[t.strftime("%Y-%m")].iloc[0]))
    R["chuva"][n]["clim_mes_mm"] = round(float(clim.loc[t.month, "mean"]))

fig, ax = plt.subplots(1, 2, figsize=(7.0, 2.25), gridspec_kw={"width_ratios": [1, 1.25]})
a = ax[0]
x = np.arange(1, 13)
sec = np.isin(x, seca_m)
a.bar(x, clim["mean"], color=np.where(sec, "#d95f02", "#1b6ca8"), width=.7, yerr=clim["std"],
      error_kw={"lw": .6, "capsize": 1.5, "ecolor": "#333"})
a.axhline(media_mes, color="k", lw=.7, ls="--")
a.set_xticks(x, list("JFMAMJJASOND"))
a.set_ylabel("Precipitação mensal (mm)")
a.set_xlim(.4, 12.6)
a.set_title("(a) Climatologia CHIRPS, 1981–2025", fontsize=8, loc="left")
a.legend(handles=[mp.Patch(color="#1b6ca8", label="época chuvosa (out–mar)"),
                  mp.Patch(color="#d95f02", label="época seca (abr–set)"),
                  plt.Line2D([], [], color="k", lw=.7, ls="--", label=f"média anual/12 = {media_mes:.0f} mm")],
         fontsize=6.5, frameon=False, loc="upper center")
a.set_ylim(0, 440)
b = ax[1]
m24 = mes["2024"]
b.bar(x, m24.values, color="#9aa5b1", width=.7, label="2024")
b.plot(x, clim["mean"].values, "k-o", ms=2.5, lw=.8, label="média 1981–2025")
for n, c in (("seca", "#d95f02"), ("chuvosa", "#1b6ca8")):
    t = pd.Timestamp(DATAS[n])
    xx = t.month - .5 + (t.day - .5) / t.days_in_month
    b.axvline(xx, color=c, lw=1.6, zorder=5)
    b.text(xx + .12 if n == "seca" else xx - .12, 436,
           f"{t.strftime('%d/%m')}\n{R['chuva'][n]['p30']:.0f} mm em 30 d", color=c, fontsize=6.5,
           ha="left" if n == "seca" else "right", va="top")
b.set_xticks(x, list("JFMAMJJASOND"))
b.set_xlim(.4, 12.6)
b.set_ylim(0, 440)
b.set_title("(b) 2024 e as datas das imagens Sentinel-2", fontsize=8, loc="left")
b.legend(fontsize=6.5, frameon=False, loc="upper center", bbox_to_anchor=(.5, .66))
for q in ax:
    q.spines[["top", "right"]].set_visible(False)
    q.tick_params(width=.5, length=2.5)
plt.tight_layout(pad=.4)
plt.savefig(F / "fig_precip.pdf")
plt.close()

# ---------- imagens ----------
sit = gpd.read_file(D / "sitio.geojson")
app = gpd.read_file(D / "fbds_recorte.gpkg")
nasc = app[app.classe == "nascente"].copy()
app_c = app[app.classe.isin(["curso", "rio_duplo"])]
with rasterio.open(D / "s2_seca.tif") as r:
    T, sh, L, Bt = r.transform, (r.height, r.width), r.bounds.left, r.bounds.top


def rz(g):
    return rasterize(g.geometry, out_shape=sh, transform=T, fill=0, default_value=1).astype(bool)


m_s = rz(sit)
m_a = rz(app_c)
m_n = rz(gpd.GeoDataFrame(geometry=nasc.buffer(50), crs=app.crs))


def ha(m):
    return m.sum() * 100 / 1e4


R["sitio"] = {"area_ha": round(ha(m_s), 1), "app_curso_ha": round(ha(m_s & m_a), 1),
              "app_curso_pct": round(100 * (m_s & m_a).sum() / m_s.sum(), 1),
              "nascentes_dentro": int(nasc.within(sit.geometry.iloc[0]).sum()),
              "app_curso_ou_nascente_pct": round(100 * (m_s & (m_a | m_n)).sum() / m_s.sum(), 1)}
with rasterio.open(D / "jrc_gsw.tif") as g:
    gs = g.read(1, out_shape=sh, resampling=rasterio.enums.Resampling.nearest).astype(float)
ind = {}
for n in DATAS:
    with rasterio.open(D / f"s2_{n}.tif") as r:
        b2, b3, b4, b8, b11, scl = r.read().astype(float)
    ok = ~np.isin(scl, [0, 1, 3, 8, 9, 10])
    ind[n] = dict(rgb=np.clip(np.dstack([b4, b3, b2]) / 3000, 0, 1) ** .8, swir=np.clip((np.dstack([b11, b8, b4]) / np.array([4500, 5500, 2500])) ** .7, 0, 1), ndwi=(b3 - b8) / (b3 + b8), mndwi=(b3 - b11) / (b3 + b11), ndmi=(b8 - b11) / (b8 + b11), ok=ok)
# limiar: Otsu do histograma da janela sem os pixels dominados por vegetação (NDWI <= -0,35), um por data
for n, v in ind.items():
    v["t"] = float(threshold_otsu(v["ndwi"][v["ok"] & (v["ndwi"] > -.35)]))
    v["agua"] = v["ok"] & (v["ndwi"] > v["t"])
pool = np.concatenate([v["ndmi"][m_s] for v in ind.values()])
t_umid = float(threshold_otsu(pool))
R["limiares"] = {"otsu_ndwi": {n: round(v["t"], 3) for n, v in ind.items()}, "otsu_ndmi_conjunto_sitio": round(t_umid, 3)}
for n, v in ind.items():
    v["umido"] = v["ok"] & (v["ndmi"] > t_umid)
    s = {"nuvem_sitio_px": int((~v["ok"] & m_s).sum()),
         "agua_janela_ha": round(ha(v["agua"]), 1), "agua_sitio_ha": round(ha(v["agua"] & m_s), 2),
         "agua_janela_t0_ha": round(ha(v["ok"] & (v["ndwi"] > 0)), 1),
         "agua_janela_tm01_ha": round(ha(v["ok"] & (v["ndwi"] > -.1)), 1),
         "sitio_px_ndwi_gt_m02": int((v["ok"] & (v["ndwi"] > -.2) & m_s).sum()),
         "ndwi_max_sitio": round(float(v["ndwi"][m_s].max()), 2),
         "mndwi_max_sitio": round(float(v["mndwi"][m_s].max()), 2)}
    for k in ("ndwi", "mndwi", "ndmi"):
        s[k + "_sitio_p5_50_95"] = [round(float(z), 2) for z in np.percentile(v[k][m_s], [5, 50, 95])]
        s[k + "_app_p50"] = round(float(np.median(v[k][m_s & m_a])), 2)
        s[k + "_foraapp_p50"] = round(float(np.median(v[k][m_s & ~m_a])), 2)
    s["umido_sitio_pct"] = round(100 * (v["umido"] & m_s).sum() / m_s.sum(), 1)
    s["umido_app_pct"] = round(100 * (v["umido"] & m_s & m_a).sum() / (m_s & m_a).sum(), 1)
    s["umido_foraapp_pct"] = round(100 * (v["umido"] & m_s & ~m_a).sum() / (m_s & ~m_a).sum(), 1)
    # referência independente: JRC Global Surface Water (1984-2021), ocorrência >= 50% = água quase permanente
    gp = gs >= 50
    s["jrc_perm_janela_ha"] = round(ha(gp), 1)
    s["agua_dentro_jrc_pct"] = round(100 * (v["agua"] & gp).sum() / max(v["agua"].sum(), 1), 1)
    s["jrc_recuperado_pct"] = round(100 * (v["agua"] & gp).sum() / max(gp.sum(), 1), 1)
    # referência principal: massas d'água artificiais e rio de margem dupla da FBDS (1:25.000)
    fb = {"massa": rz(app[app.classe == "massa_artificial"]), "rio_duplo": rz(app[app.classe == "rio_duplo"])}
    for k, mk in fb.items():
        s[f"fbds_{k}_ha"] = round(ha(mk), 1)
        s[f"fbds_{k}_detectado_pct"] = round(100 * (v["agua"] & mk).sum() / max(mk.sum(), 1), 1)
    zona = rz(gpd.GeoDataFrame(geometry=app[app.classe == "massa_artificial"].buffer(30), crs=app.crs))
    s["agua_janela_a_menos_30m_massa_pct"] = round(100 * (v["agua"] & zona).sum() / max(v["agua"].sum(), 1), 1)
    R[n] = s
# sensibilidade à posição do sítio (incerteza ~250 m): deslocamentos em 8 direções e buffer de 250 m
from shapely import affinity
g0 = sit.geometry.iloc[0]
vars_ = {f"desloc_{dx}_{dy}": affinity.translate(g0, 250 * dx, 250 * dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx, dy) != (0, 0)}
vars_["buffer_250"] = g0.buffer(250)
R["posicao"] = {}
for k, gg in vars_.items():
    mm = rz(gpd.GeoDataFrame(geometry=[gg], crs=sit.crs))
    R["posicao"][k] = {n: int((ind[n]["agua"] & mm).sum()) for n in DATAS}
R["posicao_max_px_agua"] = max(max(v.values()) for v in R["posicao"].values())
R["delta_med_sitio"] = {k: round(float(np.median(ind["chuvosa"][k][m_s] - ind["seca"][k][m_s])), 2)
                        for k in ("ndwi", "mndwi", "ndmi")}
json.dump(R, open(D / "resultados.json", "w"), indent=1, ensure_ascii=False)

# ---------- figura: RGB real, SWIR falsa-cor e NDWI, nas duas datas ----------
x0, x1, y0, y1 = 446650, 451850, 7381350, 7383950
ext = (L, L + sh[1] * 10, Bt - sh[0] * 10, Bt)
xc = np.linspace(ext[0] + 5, ext[1] - 5, sh[1])
yc = np.linspace(ext[3] - 5, ext[2] + 5, sh[0])
from pyproj import Transformer
_ida = Transformer.from_crs(4326, 31983, always_xy=True)
_volta = Transformer.from_crs(31983, 4326, always_xy=True)
_lo = [_volta.transform(x, y) for x in (x0, x1) for y in (y0, y1)]
lon_min, lon_max = min(z[0] for z in _lo), max(z[0] for z in _lo)
lat_min, lat_max = min(z[1] for z in _lo), max(z[1] for z in _lo)
lons = np.arange(np.ceil(lon_min * 100) / 100, lon_max, .01)
lats = np.arange(np.ceil(lat_min * 200) / 200, lat_max, .005)
fmt = lambda v, h: f"{abs(v):.{2 if h == 'O' else 3}f}°{h}".replace(".", ",")
fig, ax = plt.subplots(2, 3, figsize=(7.0, 3.1))
norm = TwoSlopeNorm(vmin=-.8, vcenter=-.2, vmax=.5)
cols = ["RGB (B4, B3, B2)", "SWIR falsa-cor (B11, B8, B4)", "NDWI"]
for i, (n, lab) in enumerate((("seca", "seca, 23/08/2024"), ("chuvosa", "chuvosa, 31/03/2024"))):
    v = ind[n]
    for j in range(3):
        q = ax[i, j]
        if j == 0:
            q.imshow(v["rgb"], extent=ext, interpolation="nearest")
        elif j == 1:
            q.imshow(v["swir"], extent=ext, interpolation="nearest")
        else:
            im = q.imshow(np.where(v["ok"], v["ndwi"], np.nan), extent=ext, cmap="BrBG", norm=norm, interpolation="nearest")
            q.contour(xc, yc, v["agua"].astype(float), [.5], colors="#0b3d91", linewidths=.6)
        xs, ys = sit.geometry.iloc[0].exterior.xy
        q.plot(xs, ys, color="yellow" if j < 2 else "k", lw=.9)
        q.set_xlim(x0, x1)
        q.set_ylim(y0, y1)
        for lo in lons:  # grade em graus (linhas reprojetadas para UTM 23S)
            gx, gy = _ida.transform([lo, lo], [lat_min, lat_max])
            q.plot(gx, gy, color="w", lw=.3, alpha=.7)
        for la in lats:
            gx, gy = _ida.transform([lon_min, lon_max], [la, la])
            q.plot(gx, gy, color="w", lw=.3, alpha=.7)
        q.set_xlim(x0, x1)
        q.set_ylim(y0, y1)
        q.set_xticks([_ida.transform(lo, lat_min)[0] for lo in lons] if i == 1 else [])
        q.set_xticklabels([fmt(lo, "O") for lo in lons] if i == 1 else [], fontsize=5.5)
        q.set_yticks([_ida.transform(lon_min, la)[1] for la in lats] if j == 0 else [])
        q.set_yticklabels([fmt(la, "S") for la in lats] if j == 0 else [], fontsize=5.5)
        q.tick_params(length=2, width=.4, pad=1.5)
        q.set_title(f"({'abcdef'[3 * i + j]}) {cols[j]}", fontsize=7, loc="left", pad=2)
        q.annotate("", xy=(x1 - 160, y1 - 110), xytext=(x1 - 160, y1 - 520), arrowprops=dict(arrowstyle="-|>", lw=.8, color="w" if j < 2 else "k"))
        q.text(x1 - 160, y1 - 560, "N", ha="center", va="top", fontsize=6.5, color="w" if j < 2 else "k")
        q.text(x0 + 120, y1 - 120, lab, color="w", fontsize=6.5, va="top", bbox=dict(fc="k", alpha=.5, lw=0, pad=1.5))
    ax[i, 0].plot([x0 + 200, x0 + 1200], [y0 + 170] * 2, "w-", lw=2)
    ax[i, 0].text(x0 + 700, y0 + 260, "1 km", ha="center", color="w", fontsize=6)
fig.tight_layout(pad=.3, w_pad=.4, h_pad=.6)
cb = fig.colorbar(im, ax=ax[:, 2], fraction=.04, pad=.01)
cb.ax.tick_params(labelsize=6)
fig.savefig(F / "fig_ndwi.pdf", bbox_inches="tight", pad_inches=.03)
plt.close()
print(json.dumps(R, indent=1, ensure_ascii=False))
