import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
import json
import os

gpkg_path    = "../raw_data/geoRus/gadm41_RUS.gpkg"
fire_path    = "../raw_data/Fire/Fire.csv"
output_path  = "../regions_fire"
os.makedirs(output_path, exist_ok=True)

regions_layer = "ADM_ADM_2"
regions_gdf   = gpd.read_file(gpkg_path, layer=regions_layer).to_crs("EPSG:4326")
regions_sindex = regions_gdf.sindex

def find_region(lon: float, lat: float) -> str:
    """Возвращает NAME_1, если точка попадает в полигон, иначе None."""
    pt = Point(lon, lat)
    for idx in regions_sindex.intersection(pt.bounds):
        if regions_gdf.iloc[idx].geometry.contains(pt):
            return regions_gdf.iloc[idx]["NAME_1"]
    return None

fire_types = [
    'Природный пожар',
    'Лесной пожар',
    'Контролируемый пал',
    'Неконтролируемый пал',
    'Торфяной пожар',
]

sakha_data = {
    "fire_stats": { "total": 0, **{t: 0 for t in fire_types} },
    "fires":      { t: [] for t in fire_types }
}

chunksize = 50000
num = 1
with pd.read_csv(fire_path, sep=';', chunksize=chunksize) as reader:
    for chunk in reader:
        print(num)
        num += 1
        for _, row in chunk.iterrows():
            lon, lat = row['lon'], row['lat']
            typ       = row['type_name'].strip()
            if typ not in fire_types:
                continue

            region = find_region(lon, lat)
            if region and  region == "Sakha":
                sakha_data["fire_stats"]["total"] += 1
                sakha_data["fire_stats"][typ]   += 1
                sakha_data["fires"][typ].append([lon, lat])

out_file = os.path.join(output_path, "Sakha.json")
with open(out_file, 'w', encoding='utf-8') as f:
    json.dump(sakha_data, f, ensure_ascii=False, indent=4)

print(f"Собрано {sakha_data['fire_stats']['total']} пожаров для Sakha → {out_file}")
