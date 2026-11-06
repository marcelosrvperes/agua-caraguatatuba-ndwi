# Precipitação e NDWI em um sítio de Caraguatatuba (SP): épocas seca e chuvosa

Código e dados do artigo submetido ao XXII SBSR (2027). Dados abertos processados no Google Earth Engine (GEE).

## Parâmetros
| Item | Valor |
|---|---|
| Sítio | retângulo de 3.625 m × 610 m, rumo 103°, centro em 23,667° S, 45,494° O (`dados/sitio.geojson`); posição incerta em cerca de 250 m |
| Chuva | `UCSB-CHG/CHIRPS/DAILY`, 1981-2025, média em 3 km do centro |
| Épocas | seca = mês com média abaixo de (chuva anual média)/12 |
| Imagens | `COPERNICUS/S2_SR_HARMONIZED`, tile 23KMP, 2018-2025; datas 2024-08-23 (seca) e 2024-03-31 (chuvosa) |
| Máscara de nuvem | SCL = 0, 1, 3, 8, 9, 10 (cena aceita com menos de 1% disso em 2,5 km do centro) |
| Índice e limiar | NDWI (McFeeters) = (B3-B8)/(B3+B8), 10 m; limiar de Otsu por data (janela de 8 km, sem NDWI <= -0,35) |
| Referências | FBDS 1:25.000 (`dados/fbds_recorte.gpkg`); JRC `JRC/GSW1_4/GlobalSurfaceWater` |

## Como rodar
1. Python 3.12: `pip install -r requirements.txt`.
2. `earthengine authenticate` e `set EE_PROJECT=<seu projeto GEE>` (PowerShell: `$env:EE_PROJECT="..."`).
3. Em ordem: `scripts/02_precipitacao.py`, `03_candidatas.py`, `04_baixar_s2.py`, `05_analise.py` (resultados em `dados/resultados.json` e figuras em `figuras/`), `06_mapa_localizacao.py`.
   `01_sitio.py` refaz o polígono e o recorte da FBDS a partir de um arquivo local da FBDS; o resultado já está em `dados/` e o passo pode ser pulado.

Versões das coleções: as de GEE acima (S2 SR harmonizado; CHIRPS diário v2.0; GSW 1.4), consultadas em 2026-11-05. Python: earthengine-api 1.7, geopandas 1.1, rasterio 1.5, scikit-image 0.26.

## Licença
Código sob licença MIT (`LICENSE`). Dados derivados: IBGE, FBDS, CHIRPS, Copernicus Sentinel-2 e JRC têm termos próprios de uso aberto.

## Declaração de uso de IA
O código e o texto foram feitos com o assistente Claude (Anthropic) sob direção dos autores.
