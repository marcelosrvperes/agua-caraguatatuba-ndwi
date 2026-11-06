"""Mapa de localização do sítio: Brasil (UFs), estado de São Paulo e município de Caraguatatuba.
Malhas do IBGE (API de malhas v3, baixadas em dados/ibge_*.geojson). Saída: figuras/fig_local.pdf."""
from pathlib import Path

import geopandas as gpd
import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

RAIZ = Path(__file__).resolve().parents[1]
D, F = RAIZ / "dados", RAIZ / "figuras"
plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif"], "font.size": 7})
ufs = gpd.read_file(D / "ibge_ufs.geojson")
sp = gpd.read_file(D / "ibge_sp.geojson")
mun = gpd.read_file(D / "ibge_sp_mun.geojson")
cg = gpd.read_file(D / "ibge_caragua.geojson")
sit = gpd.read_file(D / "sitio_wgs84.geojson")
sc = sit.geometry.iloc[0].centroid
AZUL, VERM = "#1b6ca8", "#d62728"


def graticula(q, passo, fmt="{:.0f}"):
    x0, x1 = q.get_xlim()
    y0, y1 = q.get_ylim()
    xs = np.arange(np.ceil(x0 / passo) * passo, x1, passo)
    ys = np.arange(np.ceil(y0 / passo) * passo, y1, passo)
    q.set_xticks(xs, [fmt.format(abs(v)) + "°O" for v in xs])
    q.set_yticks(ys, [fmt.format(abs(v)) + "°S" for v in ys])
    q.grid(color="#999", lw=.3, alpha=.7)
    q.tick_params(labelsize=6, length=2, width=.4)


def norte(q, x=.93, y=.88):
    q.annotate("", xy=(x, y), xytext=(x, y - .17), xycoords="axes fraction", arrowprops=dict(arrowstyle="-|>", lw=.8))
    q.text(x, y + .01, "N", transform=q.transAxes, ha="center", va="bottom", fontsize=7)


fig, ax = plt.subplots(1, 3, figsize=(7.0, 2.35), gridspec_kw={"width_ratios": [1, 1.1, 1.25]})
a, b, c = ax
ufs.plot(ax=a, facecolor="#eeeeee", edgecolor="#777", lw=.3)
sp.plot(ax=a, facecolor="#f4b183", edgecolor="k", lw=.5)
a.set_xlim(-74, -34)
a.set_ylim(-34, 6)
a.set_aspect(1)
graticula(a, 10)
a.text(-57, -2, "BRASIL", fontsize=7, ha="center", weight="bold")
a.annotate("SP", xy=(-49, -22), xytext=(-62, -29), fontsize=7, weight="bold", arrowprops=dict(arrowstyle="-", lw=.5))
a.set_title("(a) Brasil", fontsize=8, loc="left")

mun.plot(ax=b, facecolor="#fafafa", edgecolor="#bbb", lw=.2)
sp.boundary.plot(ax=b, color="k", lw=.6)
cg.plot(ax=b, facecolor=AZUL, edgecolor=AZUL, lw=.4)
b.plot(sc.x, sc.y, marker="o", ms=5, mfc="none", mec=VERM, mew=1)
b.set_xlim(-53.4, -44)
b.set_ylim(-25.5, -19.6)
b.set_aspect(1)
graticula(b, 2)
b.annotate("Caraguatatuba", xy=(-45.4, -23.6), xytext=(-51.2, -25.0), fontsize=6.5, color=AZUL,
           arrowprops=dict(arrowstyle="-", lw=.5, color=AZUL))
b.text(-49.6, -22.3, "SÃO PAULO", fontsize=7, ha="center", weight="bold")
b.set_title("(b) Estado de São Paulo", fontsize=8, loc="left")

cg.plot(ax=c, facecolor="#e8f1f8", edgecolor=AZUL, lw=.7)
sit.boundary.plot(ax=c, color=VERM, lw=1.2)
c.plot(sc.x, sc.y, marker="o", ms=9, mfc="none", mec=VERM, mew=.8)
c.annotate("sítio (3,6 km × 0,6 km)", xy=(sc.x, sc.y), xytext=(-45.62, -23.72), fontsize=6.5, color=VERM,
           arrowprops=dict(arrowstyle="-", lw=.5, color=VERM))
c.set_xlim(-45.75, -45.23)
c.set_ylim(-23.78, -23.46)
c.set_aspect(1)
graticula(c, .1, "{:.1f}")
c.set_title("(c) Caraguatatuba", fontsize=8, loc="left")
for q in (a, b, c):
    norte(q)
fig.tight_layout(pad=.3, w_pad=.6)
fig.savefig(F / "fig_local.pdf", bbox_inches="tight", pad_inches=.03)
fig.savefig(D / "_prev_local.png", dpi=120)
